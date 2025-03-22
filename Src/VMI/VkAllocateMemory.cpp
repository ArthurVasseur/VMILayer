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
	const auto* dp = VulkanMemoryInspector::GetInstance().GetDeviceDispatchTable(device);
	if (!dp)
	{
		CCT_ASSERT_FALSE("Could not get the device dispatch table");
		return VK_ERROR_INVALID_EXTERNAL_HANDLE;
	}

	VkResult result = dp->AllocateMemory(device, pAllocateInfo, pAllocator, pMemory);

	duckdb::Connection& conn = VulkanMemoryInspector::GetInstance().GetDataBaseConnection();

	std::string json_params = "{ \"allocationSize\": " + std::to_string(pAllocateInfo->allocationSize) +
		", \"memoryTypeIndex\": " + std::to_string(pAllocateInfo->memoryTypeIndex) + " }";

	duckdb::timestamp_t timestamp(current_timestamp());
	int frame_number = 0;

	cct::Int64 mem_delta = (result == VK_SUCCESS ? static_cast<cct::Int64>(pAllocateInfo->allocationSize) : 0);

	auto stmt = conn.Prepare(
		"INSERT INTO vulkan_events (id, timestamp, frame_number, function_name, event_type, memory_delta, parameters, result_code, thread_id) "
		"VALUES (nextval('seq_vulkan_event_id'), $1, $2, $3, $4, $5, $6, $7, $8);");
	std::stringstream threadId;
	threadId << std::this_thread::get_id();

	auto queryResult = stmt->Execute(timestamp, frame_number, "vkAllocateMemory", "allocation", mem_delta, json_params, static_cast<cct::Int64>(result), threadId.str());
	if (queryResult && queryResult->HasError())
	{
		CCT_ASSERT_FALSE("Query failed with error: '{}'", queryResult->GetError());
	}
	return result;
}

void vkFreeMemory(VkDevice device, VkDeviceMemory memory, const VkAllocationCallbacks* pAllocator)
{
	const auto* dp = VulkanMemoryInspector::GetInstance().GetDeviceDispatchTable(device);
	if (!dp)
	{
		CCT_ASSERT_FALSE("Could not get the device dispatch table");
		return;
	}

	dp->FreeMemory(device, memory, pAllocator);

	duckdb::Connection& conn = VulkanMemoryInspector::GetInstance().GetDataBaseConnection();

	std::string json_params = "{ \"memory\": " + std::to_string(reinterpret_cast<uintptr_t>(memory)) + " }";
	duckdb::timestamp_t timestamp(current_timestamp());
	int frame_number = 0;
	cct::Int64 mem_delta = 0; // If you tracked allocation size elsewhere, you might log a negative delta.

	auto stmt = conn.Prepare(
		"INSERT INTO vulkan_events (id, timestamp, frame_number, function_name, event_type, memory_delta, parameters, result_code, thread_id) "
		"VALUES (nextval('seq_vulkan_event_id'), ?, ?, ?, ?, ?, ?, ?, ?);");
	std::stringstream threadId;
	threadId << std::this_thread::get_id();

	// vkFreeMemory returns void; here we log a result code of 0.
	auto queryResult = stmt->Execute(timestamp, frame_number, "vkFreeMemory", "free", mem_delta, json_params, static_cast<cct::Int64>(0), threadId.str());
	if (queryResult && queryResult->HasError())
	{
		CCT_ASSERT_FALSE("Query failed with error: '{}'", queryResult->GetError());
	}
}

VkResult vkBindBufferMemory(VkDevice device, VkBuffer buffer, VkDeviceMemory memory, VkDeviceSize memoryOffset)
{
	const auto* dp = VulkanMemoryInspector::GetInstance().GetDeviceDispatchTable(device);
	if (!dp)
	{
		CCT_ASSERT_FALSE("Could not get the device dispatch table");
		return VK_ERROR_INVALID_EXTERNAL_HANDLE;
	}

	VkResult result = dp->BindBufferMemory(device, buffer, memory, memoryOffset);

	duckdb::Connection& conn = VulkanMemoryInspector::GetInstance().GetDataBaseConnection();

	// Build JSON-like string of parameters.
	std::string json_params = "{ \"buffer\": " + std::to_string(reinterpret_cast<uintptr_t>(buffer)) +
		", \"memory\": " + std::to_string(reinterpret_cast<uintptr_t>(memory)) +
		", \"offset\": " + std::to_string(memoryOffset) + " }";
	duckdb::timestamp_t timestamp(current_timestamp());
	int frame_number = 0;
	cct::Int64 mem_delta = 0; // Binding does not change allocation size.

	auto stmt = conn.Prepare(
		"INSERT INTO vulkan_events (id, timestamp, frame_number, function_name, event_type, memory_delta, parameters, result_code, thread_id) "
		"VALUES (nextval('seq_vulkan_event_id'), ?, ?, ?, ?, ?, ?, ?, ?);");
	std::stringstream threadId;
	threadId << std::this_thread::get_id();

	auto queryResult = stmt->Execute(timestamp, frame_number, "vkBindBufferMemory", "binding", mem_delta, json_params, static_cast<cct::Int64>(result), threadId.str());
	if (queryResult && queryResult->HasError())
	{
		CCT_ASSERT_FALSE("Query failed with error: '{}'", queryResult->GetError());
	}
	return result;
}

VkResult vkBindImageMemory(VkDevice device, VkImage image, VkDeviceMemory memory, VkDeviceSize memoryOffset)
{
	const auto* dp = VulkanMemoryInspector::GetInstance().GetDeviceDispatchTable(device);
	if (!dp)
	{
		CCT_ASSERT_FALSE("Could not get the device dispatch table");
		return VK_ERROR_INVALID_EXTERNAL_HANDLE;
	}

	VkResult result = dp->BindImageMemory(device, image, memory, memoryOffset);

	duckdb::Connection& conn = VulkanMemoryInspector::GetInstance().GetDataBaseConnection();

	std::string json_params = "{ \"image\": " + std::to_string(reinterpret_cast<uintptr_t>(image)) +
		", \"memory\": " + std::to_string(reinterpret_cast<uintptr_t>(memory)) +
		", \"offset\": " + std::to_string(memoryOffset) + " }";
	duckdb::timestamp_t timestamp(current_timestamp());
	int frame_number = 0;
	cct::Int64 mem_delta = 0;

	auto stmt = conn.Prepare(
		"INSERT INTO vulkan_events (id, timestamp, frame_number, function_name, event_type, memory_delta, parameters, result_code, thread_id) "
		"VALUES (nextval('seq_vulkan_event_id'), ?, ?, ?, ?, ?, ?, ?, ?);");
	std::stringstream threadId;
	threadId << std::this_thread::get_id();

	auto queryResult = stmt->Execute(timestamp, frame_number, "vkBindImageMemory", "binding", mem_delta, json_params, static_cast<cct::Int64>(result), threadId.str());
	if (queryResult && queryResult->HasError())
	{
		CCT_ASSERT_FALSE("Query failed with error: '{}'", queryResult->GetError());
	}
	return result;
}
