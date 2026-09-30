using System;
using System.IO;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEngine;

namespace GameLab
{
    /// <summary>
    /// Headless entry point:
    /// Unity.exe -batchmode -nographics -quit -executeMethod GameLab.BatchBuild.BuildFromOrchestrator
    /// </summary>
    public static class BatchBuild
    {
        public static void BuildFromOrchestrator()
        {
            var configPath = FindArg("-gameConfig") ?? Path.Combine(Application.dataPath, "../game_config.json");
            var outputDir = FindArg("-outputDir") ?? Path.Combine(Application.dataPath, "../../data/deliveries/latest/unity");
            var streaming = Path.Combine(Application.streamingAssetsPath, "game_config.json");
            Directory.CreateDirectory(Application.streamingAssetsPath);
            if (File.Exists(configPath))
            {
                File.Copy(configPath, streaming, true);
            }

            Directory.CreateDirectory(outputDir);
            var scenes = new[] { "Assets/Scenes/Main.unity" };
            var target = EditorUserBuildSettings.activeBuildTarget;
            if (target != BuildTarget.WebGL && target != BuildTarget.StandaloneWindows64)
            {
                target = BuildTarget.WebGL;
            }

            var options = new BuildPlayerOptions
            {
                scenes = scenes,
                locationPathName = target == BuildTarget.WebGL ? outputDir : Path.Combine(outputDir, "GameLab.exe"),
                target = target,
                options = BuildOptions.CompressWithLz4
            };
            var report = BuildPipeline.BuildPlayer(options);
            if (report.summary.result != BuildResult.Succeeded)
            {
                throw new Exception("Unity build failed: " + report.summary.result);
            }
            EditorApplication.Exit(0);
        }

        static string FindArg(string name)
        {
            var args = Environment.GetCommandLineArgs();
            foreach (var arg in args)
            {
                if (arg.StartsWith(name + "=")) return arg.Substring(name.Length + 1);
            }
            for (int i = 0; i < args.Length - 1; i++)
            {
                if (args[i] == name) return args[i + 1];
            }
            return null;
        }
    }
}
