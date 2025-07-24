#include "ALPGunSteppingAction.hh"
#include "ALPGunDetectorConstruction.hh"

#include "G4RootAnalysisManager.hh"
#include "G4Step.hh"
#include "G4Event.hh"
#include "G4RunManager.hh"
#include "G4LogicalVolume.hh"
#include "G4SystemOfUnits.hh"
#include "G4INCLGlobals.hh"
#include "G4String.hh"
#include "ALPGunTrackingInfo.hh"

ALPGunSteppingAction::ALPGunSteppingAction()
: G4UserSteppingAction(),
  fScoringVolume1(0),
  fScoringVolume2(0),
  fScoringVolume3(0)
{}

ALPGunSteppingAction::~ALPGunSteppingAction()
{}

void ALPGunSteppingAction::UserSteppingAction(const G4Step* step)
{
  /*
  fScoringVolume1 = logicWorld;
  fScoringVolume2 = logicDet;
  */

  auto analysisManager = G4RootAnalysisManager::Instance();
  // get volume of the current step
  if (!fScoringVolume1) { 
    const ALPGunDetectorConstruction* detectorConstruction
      = static_cast<const ALPGunDetectorConstruction*>
        (G4RunManager::GetRunManager()->GetUserDetectorConstruction());
    fScoringVolume1 = detectorConstruction->GetScoringVolume1();   
    fScoringVolume2 = detectorConstruction->GetScoringVolume2();   
    fScoringVolume3 = detectorConstruction->GetScoringVolume3();   
  }
  G4Track* tr = step->GetTrack();
  G4String preVolume = step->GetPreStepPoint()->GetTouchableHandle()->GetVolume()->GetLogicalVolume()->GetName();
  G4String postVolume = step->GetPostStepPoint()->GetTouchableHandle()->GetVolume() != NULL ? step->GetPostStepPoint()->GetTouchableHandle()->GetVolume()->GetLogicalVolume()->GetName() : "null";
  if ((preVolume != "Absorber") and (postVolume == "Absorber")) {
	ALPGunTrackInfo* checkInfo = dynamic_cast<ALPGunTrackInfo*>(tr->GetUserInformation());
	if (!checkInfo) {
		ALPGunTrackInfo* trackInfo = new ALPGunTrackInfo(tr->GetParticleDefinition()->GetPDGEncoding());
		tr->SetUserInformation(trackInfo);
	}
  }

  if (preVolume == "Absorber") {
    const std::vector<const G4Track*>* secondaries = step->GetSecondaryInCurrentStep();
    if (!secondaries->empty()) {
        ALPGunTrackInfo* parentInfo = dynamic_cast<ALPGunTrackInfo*>(tr->GetUserInformation());
        for (const G4Track* sec : *secondaries) {
            if (parentInfo) {
                ALPGunTrackInfo* secInfo = new ALPGunTrackInfo(parentInfo->GetTag());
                const_cast<G4Track*>(sec)->SetUserInformation(secInfo);
            }
        }
    }
    G4String postStepVolume = step->GetPostStepPoint()->GetTouchableHandle()->GetVolume()->GetLogicalVolume()->GetName();
    if (postStepVolume == "Gap") {
	    ALPGunTrackInfo* trackInfo = (ALPGunTrackInfo*)(tr->GetUserInformation());
	    analysisManager->FillNtupleDColumn(0, G4EventManager::GetEventManager()->GetConstCurrentEvent()->GetEventID());
	    analysisManager->FillNtupleDColumn(1, tr->GetParticleDefinition()->GetPDGEncoding());
	    analysisManager->FillNtupleDColumn(2, tr->GetTotalEnergy()/MeV);
	    analysisManager->FillNtupleDColumn(3, tr->GetGlobalTime()/ns);
	    analysisManager->FillNtupleDColumn(4, tr->GetPosition()[0]/mm);
	    analysisManager->FillNtupleDColumn(5, tr->GetPosition()[1]/mm);
	    analysisManager->FillNtupleDColumn(6, tr->GetPosition()[2]/mm);
	    analysisManager->FillNtupleDColumn(7, tr->GetMomentum()[0]/MeV);
	    analysisManager->FillNtupleDColumn(8, tr->GetMomentum()[1]/MeV);
	    analysisManager->FillNtupleDColumn(9, tr->GetMomentum()[2]/MeV);
	    analysisManager->FillNtupleDColumn(10, trackInfo->GetTag());
	    analysisManager->FillNtupleDColumn(11, tr->GetDefinition()->GetPDGCharge());
	    analysisManager->AddNtupleRow();
    }
  }
}

