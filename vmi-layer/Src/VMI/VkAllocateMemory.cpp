//
// Created by arthur on 01/03/2025.
//

#include "VMI/VulkanFunctions.hpp"
#include "VMI/VulkanMemoryInspector.hpp"
#include "VMI/Bindings.hpp"

// VkResult vkAllocateMemory(VkDevice device, const VkMemoryAllocateInfo* pAllocateInfo, const VkAllocationCallbacks* pAllocator, VkDeviceMemory* pMemory)
// {
// 	const auto* dp = VulkanMemoryInspector::GetInstance()->GetDeviceDispatchTable(GetKey(device));
// 	if (!dp)
// 	{
// 		CCT_ASSERT_FALSE("Could not get the device dispatch table");
// 		return VK_ERROR_INVALID_EXTERNAL_HANDLE;
// 	}

// 	VkResult result = dp->AllocateMemory(device, pAllocateInfo, pAllocator, pMemory);
// 	MemoryUsage memoryUsage = {
// 		.id = 0,
// 		.deviceMemory = reinterpret_cast<intptr_t>(*pMemory),
// 		.frameIndexAllocated = VulkanMemoryInspector::GetInstance()->GetFrameIndex(),
// 		.allocatedAt = GetCurrentTimeStamp(),
// 		.allocationSize = static_cast<cct::Int64>(pAllocateInfo->allocationSize),
// 		.frameIndexDeallocated = 0,
// 		.deallocatedAt = 0,
// 	};
// 	auto buff = Serialize(memoryUsage);
// 	VulkanMemoryInspector::GetInstance()->Send(buff);

// 	return result;
// }

// void vkFreeMemory(VkDevice device, VkDeviceMemory memory, const VkAllocationCallbacks* pAllocator)
// {
// 	const auto* dp = VulkanMemoryInspector::GetInstance()->GetDeviceDispatchTable(GetKey(device));
// 	if (!dp)
// 	{
// 		CCT_ASSERT_FALSE("Could not get the device dispatch table");
// 		return;
// 	}

// 	dp->FreeMemory(device, memory, pAllocator);

// 	MemoryUsage memoryUsage = {
// 		.id = 0,
// 		.deviceMemory = reinterpret_cast<intptr_t>(memory),
// 		.frameIndexAllocated = 0,
// 		.allocatedAt = 0,
// 		.allocationSize = 0,
// 		.frameIndexDeallocated = VulkanMemoryInspector::GetInstance()->GetFrameIndex(),
// 		.deallocatedAt = GetCurrentTimeStamp(),
// 	};
// 	auto buff = Serialize(memoryUsage);
// 	VulkanMemoryInspector::GetInstance()->Send(buff);
// }

// VkResult vkBindBufferMemory(VkDevice device, VkBuffer buffer, VkDeviceMemory memory, VkDeviceSize memoryOffset)
// {
// 	const auto* dp = VulkanMemoryInspector::GetInstance()->GetDeviceDispatchTable(GetKey(device));
// 	if (!dp)
// 	{
// 		CCT_ASSERT_FALSE("Could not get the device dispatch table");
// 		return VK_ERROR_INVALID_EXTERNAL_HANDLE;
// 	}

// 	VkResult result = dp->BindBufferMemory(device, buffer, memory, memoryOffset);

// 	return result;
// }

// VkResult vkBindImageMemory(VkDevice device, VkImage image, VkDeviceMemory memory, VkDeviceSize memoryOffset)
// {
// 	const auto* dp = VulkanMemoryInspector::GetInstance()->GetDeviceDispatchTable(GetKey(device));
// 	if (!dp)
// 	{
// 		CCT_ASSERT_FALSE("Could not get the device dispatch table");
// 		return VK_ERROR_INVALID_EXTERNAL_HANDLE;
// 	}

// 	VkResult result = dp->BindImageMemory(device, image, memory, memoryOffset);

// 	return result;
// }
