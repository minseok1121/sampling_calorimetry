#include "ALPGunDetectorConstruction.hh"

#include "G4RunManager.hh"
#include "G4NistManager.hh"
#include "G4Box.hh"
#include "G4Tubs.hh"
#include "G4Cons.hh"
#include "G4Orb.hh"
#include "G4Sphere.hh"
#include "G4Trd.hh"
#include "G4LogicalVolume.hh"
#include "G4PVPlacement.hh"
#include "G4SystemOfUnits.hh"
#include "ALPGunRunAction.hh"
ALPGunDetectorConstruction::ALPGunDetectorConstruction()
: G4VUserDetectorConstruction(),
  fScoringVolume1(0),
  fScoringVolume2(0),
  fScoringVolume3(0),
  fScoringVolume4(0),
  fScoringVolume5(0),
  detectorLength(0.),
  targetLength(0.)
{
  messenger = new G4GenericMessenger(this, "/detector/", "Detector properties");
  messenger->DeclarePropertyWithUnit("absorberLength","cm", m_absorberLength)
        .SetGuidance("Set detector absorber length")
        .SetStates(G4State_PreInit, G4State_Idle);

  messenger->DeclarePropertyWithUnit("gapLength","cm", m_gapLength)
        .SetGuidance("Set gap length")
        .SetStates(G4State_PreInit, G4State_Idle);

  messenger->DeclareProperty("numLayers", m_numLayers)
        .SetGuidance("Set number of layers")
        .SetStates(G4State_PreInit, G4State_Idle);

  messenger->DeclareProperty("absorberMaterial", m_absorber_mat)
        .SetGuidance("Set absorber material")
        .SetStates(G4State_PreInit, G4State_Idle);

  messenger->DeclarePropertyWithUnit("targetLength","cm", m_targetLength)
        .SetGuidance("Set target length")
        .SetStates(G4State_PreInit, G4State_Idle);
}

ALPGunDetectorConstruction::~ALPGunDetectorConstruction()
{
  delete messenger;
}

G4VPhysicalVolume* ALPGunDetectorConstruction::Construct()
{  

    // === Parameters ===
    G4int numLayers = m_numLayers;
    G4double absorberThickness = m_absorberLength;  // Replace with your desired x
    G4double gapThickness = m_gapLength;    // Replace with your desired y
    G4double layerThickness = absorberThickness + gapThickness;
    G4double detectorWidth = 10.0 * cm;     // Arbitrary transverse size
    targetLength = m_targetLength;
    G4double vaccLength = 30.0 * cm;
    detectorLength = numLayers * layerThickness;

    // === Materials ===
    G4NistManager* nist = G4NistManager::Instance();
    G4Material* world_mat = nist->FindOrBuildMaterial("G4_AIR");
    G4Material* absorber_mat = nist->FindOrBuildMaterial(m_absorber_mat);
    //G4Material* gap_mat = nist->FindOrBuildMaterial("G4_AIR");
// 2. Ar/CO2 70/30 Mixture (보스 코드 확인 및 가독성 개선)
G4double density = 1.66 * mg/cm3;
G4Material* ArCo2_70_30 = new G4Material("ArCo2_70_30", density, 2); // Ar과 CO2 두 분자로 구성
G4Material* CO2 = nist->FindOrBuildMaterial("G4_CARBON_DIOXIDE");
G4Material* Ar = nist->FindOrBuildMaterial("G4_Ar");
ArCo2_70_30->AddMaterial(Ar, 0.70);
ArCo2_70_30->AddMaterial(CO2, 0.30);
G4Material* gap_mat = ArCo2_70_30;

G4Material* FR4 = new G4Material("FR4", 1.86*g/cm3, 2);
FR4->AddMaterial(nist->FindOrBuildMaterial("G4_SILICON_DIOXIDE"), 0.528); // Glass
FR4->AddMaterial(nist->FindOrBuildMaterial("G4_POLYVINYL_CHLORIDE"), 0.472); // Epoxy 대용
G4Material* pcb_mat = FR4;

    G4Material* vac_mat = nist->FindOrBuildMaterial("G4_Galactic");
    G4Material* target_mat = nist->FindOrBuildMaterial("G4_W");
    G4Material* wall_mat = nist->FindOrBuildMaterial("G4_CONCRETE");
    G4Material* vCh_mat = nist->FindOrBuildMaterial("G4_STAINLESS-STEEL");
    G4Material* cu_mat = nist->FindOrBuildMaterial("G4_Cu");

    // === World Volume ===
    G4double worldSizeZ = numLayers * layerThickness + vaccLength + targetLength;
    G4Box* solidWorld = new G4Box("World", 6 * m, 6 * m, worldSizeZ);
    G4LogicalVolume* logicWorld = new G4LogicalVolume(solidWorld, world_mat, "World");
    G4VPhysicalVolume* physWorld = new G4PVPlacement(0,
                                                     G4ThreeVector(),
                                                     logicWorld,
                                                     "World",
                                                     0,
                                                     false,
                                                     0,
                                                     true);

    G4Tubs* solidWall =
      new G4Tubs("Wall",                    //its name
        3.*m, 6*m, worldSizeZ, 0, 360.0*deg); //its size

    G4LogicalVolume* logicWall =
      new G4LogicalVolume(solidWall,            //its solid
                        wall_mat,             //its material
                        "Wall");         //its name

    G4VPhysicalVolume* physWall =
      new G4PVPlacement(0,                       //no rotation
                    G4ThreeVector(0,0,0),         //at (0,0,0)
                    logicWall,                //its logical volume
                    "Wall",              //its name
                    logicWorld,              //its mother  volume
                    false,                   //no boolean operation
                    0,                       //copy number
                    true);          //overlaps checking
    
  
    G4Box* solidTarget =
      new G4Box("Target",                    //its name
          5.*cm/2, 5.*cm/2, targetLength*0.5); //its size
  
    G4LogicalVolume* logicTarget =
      new G4LogicalVolume(solidTarget,            //its solid
                          target_mat,             //its material
                          "Target");         //its name
  
    G4VPhysicalVolume* phyTarget =
      new G4PVPlacement(0,                       //no rotation
                      G4ThreeVector(0,0,-vaccLength -targetLength*0.5),         //at (0,0,0)
                      logicTarget,                //its logical volume
                      "Target",              //its name
                      logicWorld,              //its mother  volume
                      false,                   //no boolean operation
                      0,                       //copy number
                      true);          //overlaps checking
  
  
    G4Tubs* solidVacCha =
      new G4Tubs("VacCha",                    //its name
          9.7*cm, 10.0*cm, vaccLength*0.5, 0, 360.0*deg); //its size
    G4LogicalVolume* logicVacCha =
      new G4LogicalVolume(solidVacCha,            //its solid
                          vCh_mat,             //its material
                          "VacCha");         //its name
    G4VPhysicalVolume* phyVacCha =
      new G4PVPlacement(0,                       //no rotation
                      G4ThreeVector(0,0, -vaccLength*0.5),         //at (0,0,0)
                      logicVacCha,                //its logical volume
                      "VacCha",              //its name
                      logicWorld,              //its mother  volume
                      false,                   //no boolean operation
                      0,                       //copy number
                      true);          //overlaps checking
  
  
    G4Tubs* solidVac =
      new G4Tubs("Vac",                    //its name
          0.0*cm, 9.7*cm, vaccLength*0.5, 0, 360.0*deg); //its size
  
    G4LogicalVolume* logicVac =
      new G4LogicalVolume(solidVac,            //its solid
                          vac_mat,             //its material
                          "Vac");         //its name
  
    G4VPhysicalVolume* phyVac =
      new G4PVPlacement(0,                       //no rotation
                      G4ThreeVector(0,0,-vaccLength*0.5),         //at (0,0,0)
                      logicVac,                //its logical volume
                      "Vac",              //its name
                      logicWorld,              //its mother  volume
                      false,                   //no boolean operation
                      0,                       //copy number
                      true);          //overlaps checking
  
  G4double currentZ = 0.0 * cm; 

// 재료 두께 정의 (단위 주의)
G4double firstAbsThick = 2.0 * cm;
G4double firstGapThick = 0.3 * cm;  // 3mm
G4double commonGapThick = 0.3 * cm; // 3mm
G4double cuThick  = 0.1 * cm;       // 1mm
G4double pcbThick = 0.3 * cm;       // 3mm
G4double normalAbsThick = 1.0 * cm;

for (G4int i = 0; i < 6; ++i) { // 총 6개 레이어 (0번 + 반복 5번)
    
    if (i == 0) {
        // --- [Layer 0] 특수 구성 ---
        // 1. Absorber (2cm)
        currentZ += firstAbsThick / 2.0;
        G4Box* sAbs = new G4Box("Absorber", 6*cm, 6*cm, firstAbsThick/2);
        G4LogicalVolume* lAbs = new G4LogicalVolume(sAbs, absorber_mat, "Absorber");
        new G4PVPlacement(0, G4ThreeVector(0, 0, currentZ), lAbs, "Absorber", logicWorld, false, i, true);
        currentZ += firstAbsThick / 2.0;

        // 2. Gap (3mm)
        currentZ += firstGapThick / 2.0;
        G4Box* sGap = new G4Box("Gap", detectorWidth/2, detectorWidth/2, firstGapThick/2);
        G4LogicalVolume* lGap = new G4LogicalVolume(sGap, gap_mat, "Gap");
        new G4PVPlacement(0, G4ThreeVector(0, 0, currentZ), lGap, "Gap", logicWorld, false, i + 100, true);
        currentZ += firstGapThick / 2.0;

        // 3. Cu (1mm)
        currentZ += cuThick / 2.0;
        G4Box* sCu = new G4Box("Cu", detectorWidth/2, detectorWidth/2, cuThick/2);
        G4LogicalVolume* lCu = new G4LogicalVolume(sCu, cu_mat, "Cu"); // cu_mat 정의 필요
        new G4PVPlacement(0, G4ThreeVector(0, 0, currentZ), lCu, "Cu", logicWorld, false, i + 300, true);
        currentZ += cuThick / 2.0;

        // 4. PCB (3mm)
        currentZ += pcbThick / 2.0;
        G4Box* sPCB = new G4Box("PCB", detectorWidth/2, detectorWidth/2, pcbThick/2);
        G4LogicalVolume* lPCB = new G4LogicalVolume(sPCB, pcb_mat, "PCB");
        new G4PVPlacement(0, G4ThreeVector(0, 0, currentZ), lPCB, "PCB", logicWorld, false, i + 200, true);
        currentZ += pcbThick / 2.0;

    } else {
        // --- [Layer 1~5] 반복 구성 (Abs 1cm -> PCB 3mm -> Gap 3mm -> Cu 1mm -> PCB 3mm) ---
        
        // 1. Absorber (1cm)
        currentZ += normalAbsThick / 2.0;
        G4Box* sAbs = new G4Box("Absorber", detectorWidth/2, detectorWidth/2, normalAbsThick/2);
        G4LogicalVolume* lAbs = new G4LogicalVolume(sAbs, absorber_mat, "Absorber");
        new G4PVPlacement(0, G4ThreeVector(0, 0, currentZ), lAbs, "Absorber", logicWorld, false, i, true);
        currentZ += normalAbsThick / 2.0;

        // 2. PCB (3mm) - Absorber 뒤에 붙는 첫 번째 PCB
        currentZ += pcbThick / 2.0;
        G4Box* sPCB1 = new G4Box("PCB", detectorWidth/2, detectorWidth/2, pcbThick/2);
        G4LogicalVolume* lPCB1 = new G4LogicalVolume(sPCB1, pcb_mat, "PCB");
        new G4PVPlacement(0, G4ThreeVector(0, 0, currentZ), lPCB1, "PCB", logicWorld, false, i + 200, true);
        currentZ += pcbThick / 2.0;

        // 3. Gap (3mm)
        currentZ += commonGapThick / 2.0;
        G4Box* sGap = new G4Box("Gap", detectorWidth/2, detectorWidth/2, commonGapThick/2);
        G4LogicalVolume* lGap = new G4LogicalVolume(sGap, gap_mat, "Gap");
        new G4PVPlacement(0, G4ThreeVector(0, 0, currentZ), lGap, "Gap", logicWorld, false, i + 100, true);
        currentZ += commonGapThick / 2.0;

        // 4. Cu (1mm)
        currentZ += cuThick / 2.0;
        G4Box* sCu = new G4Box("Cu", detectorWidth/2, detectorWidth/2, cuThick/2);
        G4LogicalVolume* lCu = new G4LogicalVolume(sCu, cu_mat, "Cu");
        new G4PVPlacement(0, G4ThreeVector(0, 0, currentZ), lCu, "Cu", logicWorld, false, i + 300, true);
        currentZ += cuThick / 2.0;

        // 5. PCB (3mm) - Cu 뒤에 붙는 두 번째 PCB
        currentZ += pcbThick / 2.0;
        G4Box* sPCB2 = new G4Box("PCB", detectorWidth/2, detectorWidth/2, pcbThick/2);
        G4LogicalVolume* lPCB2 = new G4LogicalVolume(sPCB2, pcb_mat, "PCB");
        new G4PVPlacement(0, G4ThreeVector(0, 0, currentZ), lPCB2, "PCB", logicWorld, false, i + 400, true); // CopyNo 주의
        currentZ += pcbThick / 2.0;
    }
}
        currentZ += 24*cm / 2.0;
        G4Box* sAbs = new G4Box("Absorber", 6*cm, 6*cm, 24*cm/2);
        G4LogicalVolume* lAbs = new G4LogicalVolume(sAbs, absorber_mat, "Absorber");
        new G4PVPlacement(0, G4ThreeVector(0, 0, currentZ), lAbs, "Absorber", logicWorld, false, 11, true);
        currentZ += 24*cm / 2.0;

  
    fScoringVolume1 = logicWorld;
    fScoringVolume2 = logicTarget;
    fScoringVolume3 = logicVac;
 
    return physWorld;
}

