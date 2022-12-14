// Copyright Epic Games, Inc. All Rights Reserved.

#include "ProfilingBPLibrary.h"
#include "Profiling.h"
#include "ISessionManager.h"
#include "ISessionServicesModule.h"

UProfilingBPLibrary::UProfilingBPLibrary(const FObjectInitializer& ObjectInitializer)
: Super(ObjectInitializer)
{

}

void UProfilingBPLibrary::SendCommand(FString Command)
{
	ISessionServicesModule& SessionServicesModule = FModuleManager::LoadModuleChecked<ISessionServicesModule>("SessionServices");
	TSharedPtr<ISessionManager> SessionManager = SessionServicesModule.GetSessionManager();

	for (auto& Instance : SessionManager->GetSelectedInstances())
	{
		Instance->ExecuteCommand(Command);
		
	}
}


TArray<FString> UProfilingBPLibrary::GetLog()
{
	ISessionServicesModule& SessionServicesModule = FModuleManager::LoadModuleChecked<ISessionServicesModule>("SessionServices");
	TSharedPtr<ISessionManager> SessionManager = SessionServicesModule.GetSessionManager();
	TArray<FString> Result;
	for (auto& Instance : SessionManager->GetSelectedInstances())
	{
		for (TSharedPtr<FSessionLogMessage> i : Instance->GetLog())
		{
			Result.Push(i->Text);
		}
		
	}
	return Result;
}

