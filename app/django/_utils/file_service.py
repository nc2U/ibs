import json
from django.db import transaction
from django.core.files.storage import default_storage

class FileService:
    @staticmethod
    def manage_files(instance, initial_data, creator, file_model, related_name='meeting'):
        """
        Generic file management for models with associated file models.
        - instance: The model instance (e.g., Meeting, News)
        - initial_data: The raw request data (QueryDict)
        - creator: The user performing the action
        - file_model: The file model class (e.g., MeetingFile, NewsFile)
        - related_name: The field name in the file model pointing to the instance
        """
        
        # 1. Add new files (supports both descriptions and new_descs)
        new_files = initial_data.getlist('new_files', [])
        descriptions = initial_data.getlist('descriptions', []) or initial_data.getlist('new_descs', [])
        
        for i, upload_file in enumerate(new_files):
            file_data = {
                related_name: instance,
                'file': upload_file,
                'description': descriptions[i] if i < len(descriptions) else None,
                'creator': creator
            }
            file_model.objects.create(**file_data)

        # 2. Existing file modifications/deletions/replacements (via JSON)
        old_files = initial_data.getlist('files', [])
        cng_pks = initial_data.getlist('cngPks', [])
        cng_files = initial_data.getlist('cngFiles', [])
        cng_maps = dict(zip([str(pk) for pk in cng_pks], cng_files))

        for json_file in old_files:
            file_data = json.loads(json_file)
            pk = str(file_data.get('pk'))
            
            if file_data.get('del'):
                file_model.objects.filter(pk=pk, **{related_name: instance}).delete()
                continue

            cng_file = cng_maps.get(pk)
            if cng_file:
                try:
                    file_obj = file_model.objects.get(pk=pk, **{related_name: instance})
                    old_file_name = file_obj.file.name
                    file_obj.file = cng_file
                    file_obj.creator = creator
                    file_obj.save()
                    if old_file_name:
                        transaction.on_commit(lambda name=old_file_name: default_storage.delete(name))
                except Exception as e:
                    print(f"파일 처리 중 오류 발생: {e}")

        # 3. Single file edit (Meeting/Issue pattern)
        edit_file = initial_data.get('edit_file')
        if edit_file:
            meeting_file = file_model.objects.get(pk=edit_file, **{related_name: instance})
            old_file = None
            
            cng_file = initial_data.get('cng_file')
            if cng_file:
                old_file = meeting_file.file
                meeting_file.file = cng_file
            
            edit_file_desc = initial_data.get('edit_file_desc')
            if edit_file_desc is not None:
                meeting_file.description = edit_file_desc
            
            meeting_file.save()
            
            if old_file and old_file.name:
                transaction.on_commit(lambda f=old_file: f.delete(save=False))

        # 4. Single file deletion (direct)
        del_file = initial_data.get('del_file')
        if del_file:
            file_model.objects.filter(pk=del_file, **{related_name: instance}).delete()

        # 5. Multi-file deletion (direct)
        files_del = initial_data.getlist('files_del')
        if files_del:
            file_model.objects.filter(pk__in=files_del, **{related_name: instance}).delete()
