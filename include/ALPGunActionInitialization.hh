#ifndef ALPGunActionInitialization_h
#define ALPGunActionInitialization_h 1

#include "G4VUserActionInitialization.hh"

class ALPGunActionInitialization : public G4VUserActionInitialization
{
  public:
    ALPGunActionInitialization();
    virtual ~ALPGunActionInitialization();

    virtual void BuildForMaster() const;
    virtual void Build() const override;
};

#endif

    
