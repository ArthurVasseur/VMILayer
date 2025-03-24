//
// Created by arthur on 01/03/2025.
//

#include <vulkan/utility/vk_struct_helper.hpp>

#include "VMI/VulkanFunctions.hpp"
#include "VMI/VulkanMemoryInspector.hpp"

VkResult vkCreateInstance(const VkInstanceCreateInfo* pCreateInfo, const VkAllocationCallbacks* pAllocator, VkInstance* pInstance)
{
	VkResult result = VK_ERROR_INITIALIZATION_FAILED;

	if (pCreateInfo == nullptr)
	{
		CCT_ASSERT_FALSE("pCreateInfo is null");
		return result;
	}

	VkLayerInstanceCreateInfo* layerCreateInfo = (VkLayerInstanceCreateInfo*)pCreateInfo->pNext;

	while (layerCreateInfo && (layerCreateInfo->sType != VK_STRUCTURE_TYPE_LOADER_INSTANCE_CREATE_INFO ||
		layerCreateInfo->function != VK_LAYER_LINK_INFO))
	{
		layerCreateInfo = (VkLayerInstanceCreateInfo*)layerCreateInfo->pNext;
	}

	if (layerCreateInfo == nullptr)
	{
		CCT_ASSERT_FALSE("Could not find loader instance create info in pCreateInfo->pNext");
		return result;
	}

	PFN_vkGetInstanceProcAddr getProcAddr = layerCreateInfo->u.pLayerInfo->pfnNextGetInstanceProcAddr;
	layerCreateInfo->u.pLayerInfo = layerCreateInfo->u.pLayerInfo->pNext;

	auto createInstanceFunc = reinterpret_cast<PFN_vkCreateInstance>(getProcAddr(nullptr, "vkCreateInstance"));
	if (createInstanceFunc == nullptr)
		return VK_ERROR_INITIALIZATION_FAILED;

	VMI_GET_ALLOCATION_CALLBACKS(allocationCallbacks);

	result = createInstanceFunc(pCreateInfo, &allocationCallbacks, pInstance);
	if (result != VK_SUCCESS)
	{
		cct::Logger::Error("GEI next vkCreateInstance failed with code '{}'", static_cast<std::underlying_type_t<VkResult>>(result));
		return result;
	}

	VkuInstanceDispatchTable dispatchTable = {};
	vkuInitInstanceDispatchTable(*pInstance, &dispatchTable, getProcAddr);

	VMI_CATCH_AND_RETURN(
		VulkanMemoryInspector::GetInstance().AddInstanceDispatchTable(GetKey(*pInstance), dispatchTable);
	, VK_ERROR_INITIALIZATION_FAILED, vkCreateInstance(pCreateInfo, pAllocator, pInstance));

	cct::Logger::Error("GEI everything ok returning ");
	return VK_SUCCESS;
}
