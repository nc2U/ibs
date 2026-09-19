import Flutter
import UIKit

class SceneDelegate: FlutterSceneDelegate {
  override func scene(_ scene: UIScene, openURLContexts URLContexts: Set<UIOpenURLContext>) {
    super.scene(scene, openURLContexts: URLContexts)
    guard let url = URLContexts.first?.url else { return }

    if let appDelegate = UIApplication.shared.delegate as? FlutterAppDelegate {
      _ = appDelegate.application(
        UIApplication.shared,
        open: url,
        options: [:]
      )
    }
  }

  override func scene(
    _ scene: UIScene,
    willConnectTo session: UISceneSession,
    options connectionOptions: UIScene.ConnectionOptions
  ) {
    super.scene(scene, willConnectTo: session, options: connectionOptions)
    if let url = connectionOptions.urlContexts.first?.url {
      if let appDelegate = UIApplication.shared.delegate as? FlutterAppDelegate {
        _ = appDelegate.application(
          UIApplication.shared,
          open: url,
          options: [:]
        )
      }
    }
  }
}
