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

#include <vulkan/vulkan.h>
#include <vulkan/vk_layer.h>
#include "vulkan/utility/vk_dispatch_table.h"
#include "vulkan/utility/vk_struct_helper.hpp"

namespace vku
{
	template <> inline VkStructureType GetSType<VkLayerDeviceCreateInfo>() { return VK_STRUCTURE_TYPE_LOADER_DEVICE_CREATE_INFO; }
	template <> inline VkStructureType GetSType<VkLayerInstanceCreateInfo>() { return VK_STRUCTURE_TYPE_LOADER_INSTANCE_CREATE_INFO; }
}
#endif //GEI_DEFINES_HPP