// Copyright Epic Games, Inc. All Rights Reserved.

using UnrealBuildTool;
using System.Collections.Generic;

public class profiling_projectTarget : TargetRules
{
	public profiling_projectTarget( TargetInfo Target) : base(Target)
	{
		Type = TargetType.Game;
		DefaultBuildSettings = BuildSettingsVersion.V2;
		ExtraModuleNames.AddRange( new string[] { "profiling_project" } );
        
        if (Configuration == UnrealTargetConfiguration.Test)
        {
            GlobalDefinitions.Add("ALLOW_PROFILEGPU_IN_TEST=1");
            bUseLoggingInShipping = true;
        }
	}
}
