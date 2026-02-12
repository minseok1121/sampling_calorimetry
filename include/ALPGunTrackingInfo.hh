#include "G4VUserTrackInformation.hh"

class ALPGunTrackInfo : public G4VUserTrackInformation {
public:
    ALPGunTrackInfo(int pdg = 0, int pri = 0) : tag(pdg), pritag(pri) {}
    virtual ~ALPGunTrackInfo() {}

    void SetTag(int pdg) { tag = pdg; }
    int GetTag() const { return tag; }
    void SetPri(int pri) { pritag = pri; }
    int GetPri() const { return pritag; }

private:
    int tag;
    int pritag;
};
