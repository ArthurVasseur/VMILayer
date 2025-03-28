//
// Created by arthur on 01/03/2025.
//

#include "VMI/VulkanFunctions.hpp"
#include "VMI/VulkanMemoryInspector.hpp"

VkResult vkCreateDevice(VkPhysicalDevice physicalDevice, const VkDeviceCreateInfo* pCreateInfo, const VkAllocationCallbacks* pAllocator, VkDevice* pDevice)
{
	VkLayerDeviceCreateInfo* layerCreateInfo = (VkLayerDeviceCreateInfo*)pCreateInfo->pNext;
	while (layerCreateInfo && (layerCreateInfo->sType != VK_STRUCTURE_TYPE_LOADER_DEVICE_CREATE_INFO || layerCreateInfo->function != VK_LAYER_LINK_INFO))
	{
		layerCreateInfo = (VkLayerDeviceCreateInfo*)layerCreateInfo->pNext;
	}

	PFN_vkGetInstanceProcAddr getInstanceProcAddr = layerCreateInfo->u.pLayerInfo->pfnNextGetInstanceProcAddr;
	PFN_vkGetDeviceProcAddr getDeviceProcAddr = layerCreateInfo->u.pLayerInfo->pfnNextGetDeviceProcAddr;
	auto createDevice = reinterpret_cast<PFN_vkCreateDevice>(getInstanceProcAddr(nullptr, "vkCreateDevice"));
	if (createDevice == nullptr)
		return VK_ERROR_INITIALIZATION_FAILED;

	layerCreateInfo->u.pLayerInfo = layerCreateInfo->u.pLayerInfo->pNext;

	VkResult result = createDevice(physicalDevice, pCreateInfo, pAllocator, pDevice);
	if (result != VK_SUCCESS)
		return result;

	VkuDeviceDispatchTable dispatchTable = {};
	vkuInitDeviceDispatchTable(*pDevice, &dispatchTable, getDeviceProcAddr);

	VMI_CATCH_AND_RETURN(
		VulkanMemoryInspector::GetInstance()->AddDeviceDispatchTable(GetKey(*pDevice), dispatchTable);
	, VK_ERROR_INITIALIZATION_FAILED, vkCreateDevice(physicalDevice, pCreateInfo, pAllocator, pDevice));

	return VK_SUCCESS;
}
