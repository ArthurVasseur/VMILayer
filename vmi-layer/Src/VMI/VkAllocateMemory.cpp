//
// Created by arthur on 01/03/2025.
//

#include "VMI/VulkanFunctions.hpp"
#include "VMI/VulkanMemoryInspector.hpp"

namespace
{
	cct::Int64 current_timestamp()
	{
		using namespace std::chrono;
		auto now = system_clock::now();
		auto duration = now.time_since_epoch();
		return duration_cast<microseconds>(duration).count();
	}
}

VkResult vkAllocateMemory(VkDevice device, const VkMemoryAllocateInfo* pAllocateInfo, const VkAllocationCallbacks* pAllocator, VkDeviceMemory* pMemory)
{
	const auto* dp = VulkanMemoryInspector::GetInstance().GetDeviceDispatchTable(GetKey(device));
	if (!dp)
	{
		CCT_ASSERT_FALSE("Could not get the device dispatch table");
		return VK_ERROR_INVALID_EXTERNAL_HANDLE;
	}


	VkResult result = dp->AllocateMemory(device, pAllocateInfo, pAllocator, pMemory);
	//cct::Int64 frameCount = viewer->GetFrameCount();
	//cct::Int64 allocationSize = result == VK_SUCCESS ? static_cast<cct::Int64>(pAllocateInfo->allocationSize) : 0;

	//auto stmt = conn.Prepare(
	//	"INSERT INTO memory_usage (id, device_memory, frame_index_allocated, allocated_at, allocation_size, frame_index_deallocated, deallocated_at)"
	//	"VALUES (nextval('seq_memory_usage_id'), $1, $2, $3, $4, $5, $6);");

	//auto queryResult = stmt->Execute(reinterpret_cast<intptr_t>(*pMemory), frameCount, timestamp, allocationSize, 0, duckdb::timestamp_t(0));
	//if (queryResult && queryResult->HasError())
	//{
	//	CCT_ASSERT_FALSE("Query failed with error: '{}'", queryResult->GetError());
	//}
	return result;
}

void vkFreeMemory(VkDevice device, VkDeviceMemory memory, const VkAllocationCallbacks* pAllocator)
{
	const auto* dp = VulkanMemoryInspector::GetInstance().GetDeviceDispatchTable(GetKey(device));
	if (!dp)
	{
		CCT_ASSERT_FALSE("Could not get the device dispatch table");
		return;
	}

	dp->FreeMemory(device, memory, pAllocator);

	//duckdb::timestamp_t timestamp(current_timestamp());
	//cct::Int64 frameCount = viewer->GetFrameCount();

	//auto stmt = conn.Prepare(
	//	"UPDATE memory_usage "
	//	"SET frame_index_deallocated = $1, deallocated_at = $2 "
	//	"WHERE device_memory = $3;"
	//);

	//auto queryResult = stmt->Execute(frameCount, timestamp, reinterpret_cast<intptr_t>(memory));
	//if (queryResult && queryResult->HasError())
	//{
	//	CCT_ASSERT_FALSE("Query failed with error: '{}'", queryResult->GetError());
	//}
}

VkResult vkBindBufferMemory(VkDevice device, VkBuffer buffer, VkDeviceMemory memory, VkDeviceSize memoryOffset)
{
	const auto* dp = VulkanMemoryInspector::GetInstance().GetDeviceDispatchTable(GetKey(device));
	if (!dp)
	{
		CCT_ASSERT_FALSE("Could not get the device dispatch table");
		return VK_ERROR_INVALID_EXTERNAL_HANDLE;
	}

	VkResult result = dp->BindBufferMemory(device, buffer, memory, memoryOffset);
	
	return result;
}

VkResult vkBindImageMemory(VkDevice device, VkImage image, VkDeviceMemory memory, VkDeviceSize memoryOffset)
{
	const auto* dp = VulkanMemoryInspector::GetInstance().GetDeviceDispatchTable(GetKey(device));
	if (!dp)
	{
		CCT_ASSERT_FALSE("Could not get the device dispatch table");
		return VK_ERROR_INVALID_EXTERNAL_HANDLE;
	}

	VkResult result = dp->BindImageMemory(device, image, memory, memoryOffset);

	return result;
}
