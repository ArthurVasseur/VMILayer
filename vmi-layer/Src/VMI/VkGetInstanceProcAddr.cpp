//
// Created by arthur on 01/03/2025.
//

#include <cstring>
#include "VMI/VulkanFunctions.hpp"
#include "VMI/VulkanMemoryInspector.hpp"


PFN_vkVoidFunction vkGetInstanceProcAddr(VkInstance instance, const char* pName)
{
	VMI_GET_PROC_ADDR(vkGetInstanceProcAddr);

	VMI_GET_PROC_ADDR(vkCreateInstance);
	VMI_GET_PROC_ADDR(vkDestroyInstance);

	VMI_GET_PROC_ADDR(vkCreateDevice);
	VMI_GET_PROC_ADDR(vkDestroyDevice);
	VMI_GET_PROC_ADDR(vkQueuePresentKHR);

	const auto* dp = VulkanMemoryInspector::GetInstance()->GetInstanceDispatchTable(GetKey(instance));
	if (!dp)
		return nullptr;
	return dp->GetInstanceProcAddr(instance, pName);
}

PFN_vkVoidFunction vkGetDeviceProcAddr(VkDevice device, const char* pName)
{
	VMI_GET_PROC_ADDR(vkGetDeviceProcAddr);

	VMI_GET_PROC_ADDR(vkCreateDevice);
	VMI_GET_PROC_ADDR(vkDestroyDevice);

	VMI_GET_PROC_ADDR(vkAllocateMemory);
	VMI_GET_PROC_ADDR(vkBindBufferMemory);
	VMI_GET_PROC_ADDR(vkBindImageMemory);
	VMI_GET_PROC_ADDR(vkFreeMemory);
	VMI_GET_PROC_ADDR(vkQueuePresentKHR);

	const auto* dp = VulkanMemoryInspector::GetInstance()->GetDeviceDispatchTable(GetKey(device));
	if (!dp)
		return nullptr;
	return dp->GetDeviceProcAddr(device, pName);
}

