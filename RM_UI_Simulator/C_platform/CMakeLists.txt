cmake_minimum_required(VERSION 3.21)
project(C_platform)

# # # # # # # # # #
# 有静态链接库时调用 #
# # # # # # # # # #
#link_libraries(-lwsock32)
#link_directories(.)
#add_executable(C_platform main.c)
#target_link_libraries(C_platform libplatform.a wsock32.lib)

# # # # # # # #
# 生成静态链接库 #
# # # # # # # #
#add_library(C_platform STATIC platform.c)
#SET_TARGET_PROPERTIES(C_platform PROPERTIES OUTPUT_NAME "platform")

# # # # # # # # # #
# 无静态链接库时调用 #
# # # # # # # # # #
link_libraries(-lwsock32)
include_directories(.)
add_executable(C_platform main.c platform.h platform.c)