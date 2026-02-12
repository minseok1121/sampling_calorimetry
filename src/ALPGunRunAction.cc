#include "ALPGunRunAction.hh"
#include "ALPGunPrimaryGeneratorAction.hh"
#include "ALPGunDetectorConstruction.hh"
#include "ALPGunRun.hh"

#include "G4RootAnalysisManager.hh"
#include "G4RunManager.hh"
#include "G4LogicalVolumeStore.hh"
#include "G4LogicalVolume.hh"
#include "G4UnitsTable.hh"
#include "G4SystemOfUnits.hh"
#include "G4GenericMessenger.hh"

#include <math.h>

ALPGunRunAction::ALPGunRunAction()
: G4UserRunAction()
{
  auto analysisManager = G4RootAnalysisManager::Instance();
}

ALPGunRunAction::~ALPGunRunAction()
{}

G4Run* ALPGunRunAction::GenerateRun()
{
  return new ALPGunRun;
}

void ALPGunRunAction::BeginOfRunAction(const G4Run*)
{ 
  G4RunManager::GetRunManager()->SetRandomNumberStore(false);
  auto analysisManager = G4RootAnalysisManager::Instance();
  analysisManager->SetNtupleMerging(true);
  analysisManager->OpenFile();
  G4cout << "Using " << analysisManager->GetType() << G4endl;
  analysisManager->SetVerboseLevel(1);

  const ALPGunDetectorConstruction* detectorConstruction
   = static_cast<const ALPGunDetectorConstruction*>
     (G4RunManager::GetRunManager()->GetUserDetectorConstruction());

  analysisManager->CreateNtuple("DAMSA", "ECal");
  analysisManager->CreateNtupleDColumn("evtID");
  analysisManager->CreateNtupleDColumn("PDGID");
  analysisManager->CreateNtupleDColumn("E");
  analysisManager->CreateNtupleDColumn("t");
  analysisManager->CreateNtupleDColumn("x");
  analysisManager->CreateNtupleDColumn("y");
  analysisManager->CreateNtupleDColumn("z");
  analysisManager->CreateNtupleDColumn("px");
  analysisManager->CreateNtupleDColumn("py");
  analysisManager->CreateNtupleDColumn("pz");
  analysisManager->CreateNtupleDColumn("Mother");
  analysisManager->CreateNtupleDColumn("Charge");
  analysisManager->CreateNtupleDColumn("PPIPZ");
  analysisManager->FinishNtuple();


}

void ALPGunRunAction::EndOfRunAction(const G4Run* run)
{
  auto analysisManager = G4RootAnalysisManager::Instance();
  analysisManager->Write();
  analysisManager->CloseFile(); 
}

