cmake_minimum_required(VERSION 3.16)
project(rv2_project LANGUAGES NONE)

find_package(ament_cmake REQUIRED)
ament_package_xml()

if(NOT EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/snapshots/v${${PROJECT_NAME}_VERSION}.json")
  message(FATAL_ERROR "package.xml version has no matching snapshot")
endif()

install(DIRECTORY snapshots/
  DESTINATION share/${PROJECT_NAME}/snapshots
  FILES_MATCHING PATTERN "*.json")
install(DIRECTORY docs/
  DESTINATION share/${PROJECT_NAME}/docs
  FILES_MATCHING PATTERN "*.md")
install(FILES README.md DESTINATION share/${PROJECT_NAME})

if(BUILD_TESTING)
  find_package(ament_cmake_pytest REQUIRED)
  find_package(ament_cmake_lint_cmake REQUIRED)
  find_package(ament_cmake_xmllint REQUIRED)

  foreach(suite unit integration)
    ament_add_pytest_test(snapshot_${suite} test/${suite}
      TIMEOUT 120
      ENV
        "RV2_PROJECT_SOURCE_DIR=${CMAKE_CURRENT_SOURCE_DIR}"
        "RV2_PROJECT_SHARE_DIR=${CMAKE_INSTALL_PREFIX}/share/${PROJECT_NAME}"
        "PYTHONDONTWRITEBYTECODE=1"
        "PYTEST_ADDOPTS=-vv"
      APPEND_ENV "PYTHONPATH=${CMAKE_CURRENT_SOURCE_DIR}/test")
    set_tests_properties(snapshot_${suite} PROPERTIES LABELS "${suite}")
  endforeach()

  ament_lint_cmake(CMakeLists.txt)
  ament_xmllint(package.xml)
endif()

ament_package()
