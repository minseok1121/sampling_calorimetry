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
  /*
  if (tr->GetTrackID() == 1 && tr->GetCurrentStepNumber() == 1) {
    auto* Info = new ALPGunTrackInfo(0, 0);
    const_cast<G4Track*>(tr)->SetUserInformation(Info);
  }
    */
  
    if (tr->GetCurrentStepNumber() == 1) const_cast<G4Track*>(tr)->SetUserInformation(new ALPGunTrackInfo(tr->GetPosition().perp(), tr->GetPosition().z()));

G4String preVolume = step->GetPreStepPoint()->GetTouchableHandle()->GetVolume()->GetLogicalVolume()->GetName();
G4String postVolume = step->GetPostStepPoint()->GetTouchableHandle()->GetVolume() != NULL ? 
                     step->GetPostStepPoint()->GetTouchableHandle()->GetVolume()->GetLogicalVolume()->GetName() : "null";

                     if (preVolume == "Target") {
                      /*
                      if (tr->GetCurrentStepNumber() == 1 && tr->GetParticleDefinition()->GetPDGEncoding() == 2112 && tr->GetKineticEnergy() > 1000.0) {
                          ALPGunTrackInfo* trackInfo = (ALPGunTrackInfo*)(tr->GetUserInformation());
                          
                          // Ntuple 기록 로직 (동일)...
                          analysisManager->FillNtupleDColumn(0, G4EventManager::GetEventManager()->GetConstCurrentEvent()->GetEventID());
                          analysisManager->FillNtupleDColumn(1, tr->GetParticleDefinition()->GetPDGEncoding());
                          analysisManager->FillNtupleDColumn(2, tr->GetKineticEnergy()/MeV);
                          analysisManager->FillNtupleDColumn(3, tr->GetGlobalTime()/ns);
                          analysisManager->FillNtupleDColumn(4, tr->GetPosition()[0]/mm);
                          analysisManager->FillNtupleDColumn(5, tr->GetPosition()[1]/mm);
                          analysisManager->FillNtupleDColumn(6, tr->GetPosition()[2]/mm);
                          analysisManager->FillNtupleDColumn(7, tr->GetMomentum()[0]/MeV);
                          analysisManager->FillNtupleDColumn(8, tr->GetMomentum()[1]/MeV);
                          analysisManager->FillNtupleDColumn(9, tr->GetMomentum()[2]/MeV);
                          analysisManager->FillNtupleDColumn(10, trackInfo->GetTag());
                          analysisManager->FillNtupleDColumn(11, trackInfo->GetPri());
                          analysisManager->AddNtupleRow();
                      }
                      /*
                      if (tr->GetKineticEnergy() < 1000.0 || postVolume != "Target") {
                        tr->SetTrackStatus(fStopAndKill);
                    }
                        */
                    }

// Absorber 경계를 지날 때 (진입 시점)
if (((preVolume != "Absorber") and (postVolume == "Absorber")) || ((preVolume != "Gap") and (postVolume == "Gap"))) {
    ALPGunTrackInfo* trackInfo = (ALPGunTrackInfo*)(tr->GetUserInformation());
    
    // Ntuple 기록 로직...
    analysisManager->FillNtupleDColumn(0, G4EventManager::GetEventManager()->GetConstCurrentEvent()->GetEventID());
    analysisManager->FillNtupleDColumn(1, tr->GetParticleDefinition()->GetPDGEncoding());
    analysisManager->FillNtupleDColumn(2, tr->GetKineticEnergy()/MeV);
    analysisManager->FillNtupleDColumn(3, tr->GetGlobalTime()/ns);
    analysisManager->FillNtupleDColumn(4, tr->GetPosition()[0]/mm);
    analysisManager->FillNtupleDColumn(5, tr->GetPosition()[1]/mm);
    analysisManager->FillNtupleDColumn(6, tr->GetPosition()[2]/mm);
    analysisManager->FillNtupleDColumn(7, tr->GetMomentum()[0]/MeV);
    analysisManager->FillNtupleDColumn(8, tr->GetMomentum()[1]/MeV);
    analysisManager->FillNtupleDColumn(9, tr->GetMomentum()[2]/MeV);
    analysisManager->FillNtupleDColumn(10, trackInfo->GetTag());
    analysisManager->FillNtupleDColumn(11, trackInfo->GetPri());
    analysisManager->AddNtupleRow();
    //track->SetTrackStatus(fStopAndKill);

/*
    // --- 디버깅용 터미널 로그 ---
    G4int eventID = G4EventManager::GetEventManager()->GetConstCurrentEvent()->GetEventID();
    G4String partName = tr->GetDefinition()->GetParticleName();
    G4double energy = tr->GetKineticEnergy() / MeV;
    G4ThreeVector pos = tr->GetPosition() / mm;
    G4ThreeVector mom = tr->GetMomentum() / MeV;

    G4cout << "[DEBUG] Event: " << eventID 
           << " | Particle: " << partName << " (" << tr->GetParticleDefinition()->GetPDGEncoding() << ")"
           << " | Entering: " << postVolume 
           << " | From: " << preVolume << G4endl;
    G4cout << "        -> Energy: " << energy << " MeV"
           << " | Pos(x,y,z): (" << pos.x() << ", " << pos.y() << ", " << pos.z() << ") mm" 
           << " | Pz: " << mom.z() << " MeV" << G4endl;
    G4cout << "--------------------------------------------------------------------------------" << G4endl;
/*
    // [출력 복구] Absorber 진입 시 정보 업데이트 전 상황
    G4cout << "[Before Update] tr ID: " << tr->GetTrackID() 
           << " | Tag: " << trackInfo->GetTag() 
           << " | Pri: " << trackInfo->GetPri() << G4endl;
           */
/*
    // Pri 정보를 현재 입자의 PDG로 업데이트
    ALPGunTrackInfo* secInfo = nullptr;
    if(trackInfo->GetPri() == 0) secInfo = new ALPGunTrackInfo(trackInfo->GetTag(), tr->GetParticleDefinition()->GetPDGEncoding());
    else secInfo = new ALPGunTrackInfo(trackInfo->GetTag(), trackInfo->GetPri());
    const_cast<G4Track*>(tr)->SetUserInformation(secInfo);
*/
    // [출력 복구] 정보 업데이트 후 상황 확인
    /*
    auto* updatedInfo = dynamic_cast<ALPGunTrackInfo*>(tr->GetUserInformation());
    G4cout << "[After Update] tr ID: " << tr->GetTrackID() 
           << " | Tag: " << updatedInfo->GetTag() 
           << " | Pri: " << updatedInfo->GetPri() << G4endl;
           */
}
//if(tr->GetPosition()[2] > 0) tr->SetTrackStatus(fStopAndKill);
// Absorber 내부에서 첫 번째 스텝일 때
if (preVolume == "Absorber" || preVolume == "Gap") {
  //tr->SetTrackStatus(fStopAndKill);
    //if (tr->GetCurrentStepNumber() == 1) {
    ///*
      if (step->GetTotalEnergyDeposit() > 0) {
        ALPGunTrackInfo* trackInfo = (ALPGunTrackInfo*)(tr->GetUserInformation());
///*        
        // Ntuple 기록 로직 (동일)...
        analysisManager->FillNtupleDColumn(0, G4EventManager::GetEventManager()->GetConstCurrentEvent()->GetEventID());
        analysisManager->FillNtupleDColumn(1, tr->GetParticleDefinition()->GetPDGEncoding());
        analysisManager->FillNtupleDColumn(2, tr->GetKineticEnergy()/MeV);
        analysisManager->FillNtupleDColumn(3, tr->GetGlobalTime()/ns);
        analysisManager->FillNtupleDColumn(4, tr->GetPosition()[0]/mm);
        analysisManager->FillNtupleDColumn(5, tr->GetPosition()[1]/mm);
        analysisManager->FillNtupleDColumn(6, tr->GetPosition()[2]/mm);
        analysisManager->FillNtupleDColumn(7, tr->GetMomentum()[0]/MeV);
        analysisManager->FillNtupleDColumn(8, tr->GetMomentum()[1]/MeV);
        analysisManager->FillNtupleDColumn(9, tr->GetMomentum()[2]/MeV);
        analysisManager->FillNtupleDColumn(10, trackInfo->GetTag());
        analysisManager->FillNtupleDColumn(11, trackInfo->GetPri());
        analysisManager->FillNtupleDColumn(12, step->GetTotalEnergyDeposit());
        analysisManager->AddNtupleRow();
      }
//*/
/*
        // [신규 출력 추가] 광자(Photon) 태깅 기능 전후 확인
        if(tr->GetParticleDefinition()->GetPDGEncoding() == 22){
            auto* pInfo = dynamic_cast<ALPGunTrackInfo*>(tr->GetUserInformation());

            // Tag를 1로 강제 변경 (Pri는 유지)
            auto* secInfo = new ALPGunTrackInfo(1, pInfo->GetPri());
            const_cast<G4Track*>(tr)->SetUserInformation(secInfo);

            //G4cout << "  -> [Photon Tagging Done] New Tag: 1 | Pri: " << pInfo->GetPri() << G4endl;
        }
        */
 //   }   
}

const auto* secondaries = step->GetSecondaryInCurrentStep();
  if (secondaries && !secondaries->empty()) {
    for (const G4Track* sec : *secondaries) {
        if (sec->GetUserInformation() == nullptr) {
            //auto* pInfo = dynamic_cast<ALPGunTrackInfo*>(tr->GetUserInformation());
            /*
            if (sec->GetKineticEnergy() > 1000.0) {
              G4int evtID = G4RunManager::GetRunManager()->GetCurrentEvent()->GetEventID();
              
              // 현재 트랙(즉, Mother)의 정보
              G4Track* curTrack = step->GetTrack();
              G4int curTrackID = curTrack->GetTrackID();
              G4int parentID = curTrack->GetParentID();
              G4String momName = curTrack->GetDefinition()->GetParticleName();
              G4double momEnergyPre = step->GetPreStepPoint()->GetKineticEnergy();
          
              // 생성된 입자(Secondary) 정보
              G4String secName = sec->GetDefinition()->GetParticleName();
              G4double secEnergy = sec->GetKineticEnergy();
          
              const G4VProcess* creatorProcess = sec->GetCreatorProcess();
              G4String procName = (creatorProcess) ? creatorProcess->GetProcessName() : "Primary";
          
              G4cout << "Evt: " << evtID 
                     << " | TID: " << curTrackID << " | PID: " << parentID 
                     << " | Mother: " << momName << " (" << momEnergyPre << " MeV)"
                     << " | Secondary: " << secName << " (" << secEnergy << " MeV)"
                     << " | Process: " << procName << G4endl;
          }
                     //*/
            // [출력 복구] Secondary 생성 시 부모(Parent)의 정보 확인
            /*
            if (pInfo) {
                G4cout << "[Parent tr] ID: " << tr->GetTrackID() 
                       << " | Tag: " << pInfo->GetTag() 
                       << " | Pri: " << pInfo->GetPri() << G4endl;
            }
                       */

            //ALPGunTrackInfo* secInfo = nullptr;
                //secInfo = new ALPGunTrackInfo(pInfo->GetTag(), pInfo->GetPri());
                //secInfo = new ALPGunTrackInfo(tr->GetParticleDefinition()->GetPDGEncoding(), pInfo->GetPri());

            //const_cast<G4Track*>(sec)->SetUserInformation(secInfo);
            /*
            // [출력 복구] 새로 생성된 Secondary의 정보 확인
            auto* checkSecInfo = dynamic_cast<ALPGunTrackInfo*>(sec->GetUserInformation()); 
            if (checkSecInfo) {
                G4cout << "  -> [New sec Record Check] Tag: " << checkSecInfo->GetTag() 
                       << " | Pri: " << checkSecInfo->GetPri() << G4endl;
            }
                       */
        }
    }
}

}