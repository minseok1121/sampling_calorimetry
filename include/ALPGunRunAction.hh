#ifndef ALPGunRunAction_h
#define ALPGunRunAction_h 1

#include "G4UserRunAction.hh"
#include "globals.hh"
#include "ALPGunDetectorConstruction.hh"
class G4Run;
class G4LogicalVolume;

class ALPGunRunAction : public G4UserRunAction
{
  public:
    ALPGunRunAction();
    virtual ~ALPGunRunAction();
    virtual G4Run* GenerateRun();
    virtual void BeginOfRunAction(const G4Run*);
    virtual void EndOfRunAction(const G4Run*);
};

#endif

