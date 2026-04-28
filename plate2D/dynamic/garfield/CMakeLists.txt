cmake_minimum_required(VERSION 3.16)
project(PpcTransientSignal LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(Garfield REQUIRED)

add_executable(sim_transient sim_transient.cpp)
target_link_libraries(sim_transient PRIVATE Garfield::Garfield)
