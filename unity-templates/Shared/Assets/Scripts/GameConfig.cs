using System;
using System.IO;
using UnityEngine;

/// <summary>
/// Reads the JSON the Python orchestrator writes. Gameplay code should only
/// consume these fields — never generated C#.
/// </summary>
[Serializable]
public class GameConfig
{
    public string genre;
    public string templateId;
    public string heroName;
    public string heroColor;
    public string heroLight;
    public string heroInk;
    public string heroSilhouette;
    public string heroExtras;
    public string enemyName;
    public string enemyColor;
    public string goalText;
    public string winCondition;
    public int target;
    public string title;
    public string subtitle;
    public string winText;
    public string loseText;
    public string hint;
    public string sky;
    public string ground;
    public string fog;
    public string obstacleColor;
    public string itemColor;
    public string mood;

    public static GameConfig Load()
    {
        var path = Path.Combine(Application.streamingAssetsPath, "game_config.json");
        if (!File.Exists(path))
        {
            Debug.LogWarning("game_config.json missing — using template defaults.");
            return new GameConfig
            {
                genre = "collect",
                heroName = "Sari",
                title = "Sari's Hunt",
                target = 8,
                winText = "You did it!",
                loseText = "Almost. Try again.",
                sky = "#f0d9b5",
                ground = "#7b8f4a",
                heroColor = "#c45c26",
            };
        }
        return JsonUtility.FromJson<GameConfig>(File.ReadAllText(path));
    }

    public Color Parse(string hex, Color fallback)
    {
        if (ColorUtility.TryParseHtmlString(hex, out var color)) return color;
        return fallback;
    }
}
