#ifndef ALPGunPrimaryGeneratorAction_h
#define ALPGunPrimaryGeneratorAction_h 1

#include "G4VUserPrimaryGeneratorAction.hh"
#include "G4ParticleGun.hh"
#include "G4GenericMessenger.hh"
#include "globals.hh"

class G4ParticleGun;
class TRandom3;

class ALPGunPrimaryGeneratorAction : public G4VUserPrimaryGeneratorAction
{
  public:
    ALPGunPrimaryGeneratorAction();    
    virtual ~ALPGunPrimaryGeneratorAction();

    virtual void GeneratePrimaries(G4Event*);         
  
    const G4ParticleGun* GetParticleGun() const { return fParticleGun; }
  private:
    G4ParticleGun*  fParticleGun; // pointer a to G4 gun class
    G4GenericMessenger* messenger;
    G4ThreeVector fDir1, fDir2;
    G4double fE1, fE2;
};

#endif


