import io
import base64
from collections import deque
import pypdfium2 as pdfium
import numpy as np
from PIL import Image, ImageFilter


def _find_connected_components(binary_grid):
    """
    SciPy 없이 순수 Python deque 및 NumPy를 사용하여 연결된 요소들의 바운딩 박스를 탐색
    """
    height, width = binary_grid.shape
    visited = np.zeros((height, width), dtype=bool)
    components = []

    ys, xs = np.nonzero(binary_grid)
    for start_y, start_x in zip(ys, xs):
        if visited[start_y, start_x]:
            continue

        queue = deque([(int(start_y), int(start_x))])
        visited[start_y, start_x] = True
        min_x, max_x = int(start_x), int(start_x)
        min_y, max_y = int(start_y), int(start_y)

        while queue:
            cy, cx = queue.popleft()
            if cx < min_x:
                min_x = cx
            if cx > max_x:
                max_x = cx
            if cy < min_y:
                min_y = cy
            if cy > max_y:
                max_y = cy

            # 4-연결성 이웃 탐색
            for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                ny, nx = cy + dy, cx + dx
                if 0 <= ny < height and 0 <= nx < width:
                    if binary_grid[ny, nx] and not visited[ny, nx]:
                        visited[ny, nx] = True
                        queue.append((ny, nx))

        components.append((min_x, min_y, max_x + 1, max_y + 1))
    return components


def extract_seals_from_file(file_content_bytes, is_pdf=True, min_area=300):
    """
    스캔된 A4 PDF 또는 이미지에서 붉은색 인장들을 감지하여 각각 투명 배경 PNG 이미지로 추출 (SciPy 의존성 제로)

    Args:
        file_content_bytes (bytes): PDF 또는 이미지 파일의 바이너리
        is_pdf (bool): PDF 여부 (True면 첫 페이지를 고해상도로 렌더링)
        min_area (int): 인장으로 인정할 최소 픽셀 수

    Returns:
        List[dict]: 감지된 인장 정보 목록
    """
    # 1. 원본 이미지 로드
    if is_pdf:
        pdf = pdfium.PdfDocument(file_content_bytes)
        if len(pdf) == 0:
            raise ValueError("PDF 파일에 페이지가 없습니다.")
        page = pdf[0]
        pil_img = page.render(scale=3).to_pil().convert('RGB')
    else:
        pil_img = Image.open(io.BytesIO(file_content_bytes)).convert('RGB')

    width, height = pil_img.size
    img_np = np.array(pil_img)

    # 2. 붉은색(인주) 마스크 생성
    r = img_np[:, :, 0].astype(np.int16)
    g = img_np[:, :, 1].astype(np.int16)
    b = img_np[:, :, 2].astype(np.int16)

    # 인주 붉은색 조건: R 값이 최소 75 이상이고 G, B 대비 붉은색 차이가 뚜렷할 것
    red_diff = r - np.maximum(g, b)
    red_mask = (r >= 75) & (red_diff >= 18)

    if np.sum(red_mask) < min_area:
        raise ValueError("스캔 문서에서 붉은색 인장을 찾을 수 없습니다.")

    # 3. 도장 내부 글자와 외곽선을 하나의 덩어리로 묶기 위해 팽창(Dilation)
    # 연산 속도를 위해 4배 다운샘플링 후 Pillow MaxFilter로 팽창 연산
    step = 4
    small_mask_uint8 = (red_mask[::step, ::step].astype(np.uint8)) * 255
    pil_mask = Image.fromarray(small_mask_uint8, mode='L')
    # 9x9 MaxFilter: 인접 글자 획과 외곽선을 결합
    dilated_pil = pil_mask.filter(ImageFilter.MaxFilter(size=9))
    dilated_np = np.array(dilated_pil) > 0

    # SciPy 없이 순수 Python/NumPy BFS로 연결 요소 탐색
    raw_components = _find_connected_components(dilated_np)

    clusters = []
    for sx1, sy1, sx2, sy2 in raw_components:
        # 원래 크기로 복원
        x1, x2 = sx1 * step, sx2 * step
        y1, y2 = sy1 * step, sy2 * step
        bw, bh = x2 - x1, y2 - y1

        # 도장 크기 조건: 가로/세로 40px ~ 1200px
        if 40 <= bw <= 1200 and 40 <= bh <= 1200:
            actual_red_pixels = np.sum(red_mask[y1:y2, x1:x2])
            if actual_red_pixels >= min_area:
                clusters.append((x1, y1, x2, y2))

    if not clusters:
        raise ValueError("스캔 문서에서 유효한 크기의 인장을 감지하지 못했습니다.")

    # 4. 인접/겹치는 영역 병합 (도장 외곽선과 내부 획이 살짝 떨어진 경우 병합)
    merged_boxes = []
    for box in clusters:
        bx1, by1, bx2, by2 = box
        merged = False
        for i, m in enumerate(merged_boxes):
            mx1, my1, mx2, my2 = m
            margin = 50
            if not (bx2 + margin < mx1 or bx1 - margin > mx2 or by2 + margin < my1 or by1 - margin > my2):
                merged_boxes[i] = (min(bx1, mx1), min(by1, my1), max(bx2, mx2), max(by2, my2))
                merged = True
                break
        if not merged:
            merged_boxes.append(box)

    # Y좌표(위쪽) 순으로 정렬 (상단 인장이 1번, 하단이 2번)
    merged_boxes.sort(key=lambda b: (b[1] // 200, b[0]))

    results = []
    for idx, (bx1, by1, bx2, by2) in enumerate(merged_boxes):
        bw = bx2 - bx1
        bh = by2 - by1

        # 도장 테두리 여백(12%) 추가
        pad = int(max(bw, bh) * 0.12)
        cx1 = max(0, bx1 - pad)
        cy1 = max(0, by1 - pad)
        cx2 = min(width, bx2 + pad)
        cy2 = min(height, by2 + pad)

        crop_rgb = img_np[cy1:cy2, cx1:cx2]

        # 투명화(알파 채널) 계산
        cr = crop_rgb[:, :, 0].astype(float)
        cg = crop_rgb[:, :, 1].astype(float)
        cb = crop_rgb[:, :, 2].astype(float)

        diff = cr - (cg + cb) / 2.0
        # 자연스러운 알파 블렌딩 (인주 영역은 255 불투명, 배경 종이는 0 투명)
        alpha = np.clip((diff - 10) * 3.8, 0, 255).astype(np.uint8)

        # 인영(빨간색) 색상 보정
        out_r = np.clip(cr * 1.15, 0, 255).astype(np.uint8)
        out_g = (cg * 0.60).astype(np.uint8)
        out_b = (cb * 0.60).astype(np.uint8)

        rgba = np.dstack((out_r, out_g, out_b, alpha))
        seal_pil = Image.fromarray(rgba, mode='RGBA')

        # 알파 채널 기준으로 타이트하게 크롭(Trim)
        bbox = seal_pil.split()[-1].getbbox()
        if bbox:
            seal_pil = seal_pil.crop(bbox)

        # 정사각형 캔버스 중앙 배치
        sw, sh = seal_pil.size
        side = max(sw, sh) + int(max(sw, sh) * 0.08)
        square_canvas = Image.new('RGBA', (side, side), (255, 255, 255, 0))
        square_canvas.paste(seal_pil, ((side - sw) // 2, (side - sh) // 2), seal_pil)
        square_canvas.thumbnail((200, 200), Image.Resampling.LANCZOS)

        buf = io.BytesIO()
        square_canvas.save(buf, format='PNG')
        png_bytes = buf.getvalue()
        b64_str = base64.b64encode(png_bytes).decode('utf-8')

        pos_y_ratio = cy1 / float(height)
        pos_x_ratio = cx1 / float(width)
        y_desc = "상단" if pos_y_ratio < 0.35 else ("중단" if pos_y_ratio < 0.65 else "하단")
        x_desc = "좌측" if pos_x_ratio < 0.35 else ("우측" if pos_x_ratio > 0.65 else "중앙")

        results.append({
            'index': idx + 1,
            'position_hint': f"{y_desc} {x_desc}",
            'bbox': (cx1, cy1, cx2, cy2),
            'png_bytes': png_bytes,
            'preview_base64': f"data:image/png;base64,{b64_str}",
            'width': square_canvas.width,
            'height': square_canvas.height,
        })

    return results
