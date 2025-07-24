#include "G4VUserTrackInformation.hh"

class ALPGunTrackInfo : public G4VUserTrackInformation {
public:
    ALPGunTrackInfo(int pdg = 0) : tag(pdg) {}
    virtual ~ALPGunTrackInfo() {}

    void SetTag(int pdg) { tag = pdg; }
    int GetTag() const { return tag; }

private:
    int tag;
};
