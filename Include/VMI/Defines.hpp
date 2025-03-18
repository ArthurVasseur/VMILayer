//
// Created by arthur on 01/03/2025.
//

#ifndef GEI_DEFINES_HPP
#define GEI_DEFINES_HPP

#include <Concerto/Core/Types.hpp>
#include <Concerto/Core/Assert.hpp>

#ifdef CCT_COMPILER_MSVC
#pragma warning(disable: 4251) // Disable warning about DLL interface needed
#endif

#define VMI_EXPORT extern "C" CCT_EXPORT

#define VK_NO_PROTOTYPES
#include <vulkan/vk_layer.h>
#include <vulkan/vk_layer_dispatch_table.h>

#endif //GEI_DEFINES_HPP