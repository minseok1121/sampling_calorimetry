#ifndef ALPGunDetectorConstruction_h
#define ALPGunDetectorConstruction_h 1

#include "G4VUserDetectorConstruction.hh"
#include "G4GenericMessenger.hh"
#include "globals.hh"

class G4VPhysicalVolume;
class G4LogicalVolume;
class G4Material;

class ALPGunDetectorConstruction : public G4VUserDetectorConstruction
{
  private:
    G4GenericMessenger* messenger;
    G4double detectorLength, targetLength;
    G4double m_targetLength;
    G4double m_absorberLength, m_gapLength;
    G4int m_numLayers;
    G4String m_absorber_mat;
          
  public:
    ALPGunDetectorConstruction();
    virtual ~ALPGunDetectorConstruction();
    
    virtual G4VPhysicalVolume* Construct();
    
    G4LogicalVolume* GetScoringVolume1() const { return fScoringVolume1; }
    G4LogicalVolume* GetScoringVolume2() const { return fScoringVolume2; }
    G4LogicalVolume* GetScoringVolume3() const { return fScoringVolume3; }
    G4double GetDetectorLength() const { return detectorLength;}
    G4double GetTargetLength() const { return targetLength;}

  protected: 
    
    G4LogicalVolume*  fScoringVolume1;
    G4LogicalVolume*  fScoringVolume2;
    G4LogicalVolume*  fScoringVolume3;
    G4LogicalVolume*  fScoringVolume4;
    G4LogicalVolume*  fScoringVolume5;

};

#endif

