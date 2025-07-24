#ifndef ALPGunRun_h
#define ALPGunRun_h 1

#include "G4Run.hh"
#include "globals.hh"

class G4Event;

class ALPGunRun : public G4Run
{
  public:
    ALPGunRun();
    virtual ~ALPGunRun();
};

#endif
