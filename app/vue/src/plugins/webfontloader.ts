/**
 * plugins/webfontloader.ts
 *
 * webfontloader documentation: https://github.com/typekit/webfontloader
 */

export async function loadFonts() {
  try {
    const mod = await import('webfontloader')
    const webFontLoader = mod.default ?? mod

    webFontLoader.load({
      google: {
        families: ['Roboto:100,300,400,500,700,900&display=swap'],
      },
    })
  } catch (error) {
    console.warn('Webfont loading failed:', error)
  }
}
