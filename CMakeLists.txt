# downgrade la version minimal pour plus de comptabilité
cmake_minimum_required(VERSION 3.16) 

project(bibliotheque LANGUAGES CXX)

# Specifie qu'on veut la version C++17 du langage
set(CMAKE_CXX_STANDARD 17)

set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Explicit source list
set(SOURCES
    main.cpp
    book.cpp
    user.cpp
    library.cpp
    filemanager.cpp
)

add_executable(bibliotheque ${SOURCES})

# Enable warnings
if(MSVC)
    target_compile_options(bibliotheque PRIVATE /W4)
else()
    target_compile_options(bibliotheque PRIVATE -Wall -Wextra -Wpedantic)
endif()

# vérifie les dépendances systêmes des anciens 
include(CheckCXXSourceCompiles)
set(CMAKE_REQUIRED_FLAGS "${CMAKE_CXX_FLAGS}")
check_cxx_source_compiles("
#include <filesystem>
int main() { std::filesystem::path p{\".\"}; return p.empty(); }
" HAVE_STD_FILESYSTEM)

if(NOT HAVE_STD_FILESYSTEM)
    target_link_libraries(bibliotheque PRIVATE stdc++fs)
endif()