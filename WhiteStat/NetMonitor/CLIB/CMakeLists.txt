cmake_minimum_required(VERSION 3.0.0)
project(WhiteStat VERSION 0.1.0)

# specify the C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED True)

include_directories(.)

include(CTest)
enable_testing()

add_executable(WhiteStatProgram main.cpp)
add_library(WhiteStat SHARED main.cpp)

include(FindPCAP.cmake)
target_link_libraries(WhiteStatProgram ${PCAP_LIBRARY})
target_link_libraries(WhiteStat ${PCAP_LIBRARY})

set(THREADS_PREFER_PTHREAD_FLAG ON)
find_package(Threads REQUIRED)
target_link_libraries(WhiteStatProgram Threads::Threads)
target_link_libraries(WhiteStat Threads::Threads)

set(CPACK_PROJECT_NAME ${PROJECT_NAME})
set(CPACK_PROJECT_VERSION ${PROJECT_VERSION})
include(CPack)
