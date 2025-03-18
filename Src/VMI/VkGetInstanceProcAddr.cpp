//
// Created by arthur on 01/03/2025.
//

#include <cstring>
#include "VMI/VulkanFunctions.hpp"

#define VMI_GET_PROC_ADDR(func) if(!strcmp(pName, #func)) return (PFN_vkVoidFunction)&(func)


PFN_vkVoidFunction vkGetInstanceProcAddr(VkInstance instance, const char* pName)
{
	VMI_GET_PROC_ADDR(vkGetInstanceProcAddr);

	VMI_GET_PROC_ADDR(vkCreateInstance);
	VMI_GET_PROC_ADDR(vkDestroyInstance);

	return nullptr;
}
