cmake_minimum_required(VERSION 2.6 FATAL_ERROR)
project(ALPGun)

option(WITH_GEANT4_UIVIS "Build example with Geant4 UI and Vis drivers" OFF)
if(WITH_GEANT4_UIVIS)
  find_package(Geant4 REQUIRED ui_all vis_all)
else()
  find_package(Geant4 REQUIRED)
endif()

include(${Geant4_USE_FILE})
include_directories(${PROJECT_SOURCE_DIR}/include)

file(GLOB sources ${PROJECT_SOURCE_DIR}/src/*.cc)
file(GLOB headers ${PROJECT_SOURCE_DIR}/include/*.hh)

add_executable(ALPGun ALPGun.cc ${sources} ${headers})
target_link_libraries(ALPGun ${Geant4_LIBRARIES})

set(ALPGUN_SCRIPTS
   gun.mac
   makeJob.py
   )

foreach(_script ${ALPGUN_SCRIPTS})
  configure_file(
    ${PROJECT_SOURCE_DIR}/${_script}
    ${PROJECT_BINARY_DIR}/${_script}
    COPYONLY
    )
endforeach()

install(TARGETS ALPGun DESTINATION bin)


