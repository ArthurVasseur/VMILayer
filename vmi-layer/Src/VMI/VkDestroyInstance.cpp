//
// Created by arthur on 01/03/2025.
//


#include "VMI/VulkanFunctions.hpp"
#include "VMI/VulkanMemoryInspector.hpp"
void vkDestroyInstance(VkInstance instance, const VkAllocationCallbacks* pAllocator)
{
	auto vmiInstance = VulkanMemoryInspector::GetInstance();
	if (vmiInstance.use_count() == 1)
		VulkanMemoryInspector::DestroyInstance();
}
