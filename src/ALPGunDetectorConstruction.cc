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
    G4double detectorWidth = 12.0 * cm;     // Arbitrary transverse size
    targetLength = m_targetLength;
    G4double vaccLength = 30.0 * cm;
    detectorLength = numLayers * layerThickness;

    // === Materials ===
    G4NistManager* nist = G4NistManager::Instance();
    G4Material* world_mat = nist->FindOrBuildMaterial("G4_AIR");
    G4Material* absorber_mat = nist->FindOrBuildMaterial(m_absorber_mat);
    G4Material* gap_mat = nist->FindOrBuildMaterial("G4_AIR");
    G4Material* vac_mat = nist->FindOrBuildMaterial("G4_Galactic");
    G4Material* target_mat = nist->FindOrBuildMaterial("G4_W");
    G4Material* wall_mat = nist->FindOrBuildMaterial("G4_CONCRETE");
    G4Material* vCh_mat = nist->FindOrBuildMaterial("G4_STAINLESS-STEEL");

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
          12.*cm, 12.*cm, targetLength*0.5); //its size
  
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
  
  



    for (G4int i = 0; i < numLayers; ++i) {
        //G4double zBase = -worldSizeZ/2 + (i + 0.5) * layerThickness;
        G4double zBase = (i + 0.5) * layerThickness;
        // --- Tungsten layer ---
        G4Box* solidAbsorber = new G4Box("Absorber", detectorWidth/2, detectorWidth/2, absorberThickness/2);
        G4LogicalVolume* logicAbsorber = new G4LogicalVolume(solidAbsorber, absorber_mat, "Absorber");
        new G4PVPlacement(0, G4ThreeVector(0, 0, zBase - gapThickness/2), logicAbsorber, "Absorber", logicWorld, false, i, true);

        // --- Air gap ---
        G4Box* solidGap = new G4Box("Gap", detectorWidth/2, detectorWidth/2, gapThickness/2);
        G4LogicalVolume* logicGap = new G4LogicalVolume(solidGap, gap_mat, "Gap");
        new G4PVPlacement(0, G4ThreeVector(0, 0, zBase + absorberThickness/2), logicGap, "Gap", logicWorld, false, i + 100, true);
    }

  
    fScoringVolume1 = logicWorld;
    fScoringVolume2 = logicTarget;
    fScoringVolume3 = logicVac;
 
    return physWorld;
}

