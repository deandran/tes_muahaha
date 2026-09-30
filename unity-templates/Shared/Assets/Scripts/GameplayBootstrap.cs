using UnityEngine;

/// <summary>
/// Applies GameConfig to the scene. Gameplay lives in the template, not in
/// generated scripts.
/// </summary>
public class GameplayBootstrap : MonoBehaviour
{
    public Camera worldCamera;
    public SpriteRenderer ground;

    void Start()
    {
        var cfg = GameConfig.Load();
        if (worldCamera != null)
        {
            worldCamera.backgroundColor = cfg.Parse(cfg.sky, Color.gray);
        }
        if (ground != null)
        {
            ground.color = cfg.Parse(cfg.ground, Color.green);
        }
        Debug.Log("Loaded template " + cfg.templateId + " for " + cfg.heroName);
    }
}
