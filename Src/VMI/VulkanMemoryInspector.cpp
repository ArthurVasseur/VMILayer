//
// Created by arthur on 01/03/2025.
//

#include <mimalloc.h>

#include "VMI/VulkanMemoryInspector.hpp"

VulkanMemoryInspector VulkanMemoryInspector::instance = VulkanMemoryInspector();


VulkanMemoryInspector::VulkanMemoryInspector() :
	_allocationCallbacks({ .pUserData = nullptr,
							.pfnAllocation = &AllocationFunction,
							.pfnReallocation = &ReallocationFunction,
							.pfnFree = &FreeFunction,
							.pfnInternalAllocation = &InternalAllocationNotification,
							.pfnInternalFree = &InternalFreeNotification }),
	db(),
	dbConnection(db)
{
	auto queryResult = dbConnection.Query(R"(
			-- Table for logging intercepted Vulkan events:
			CREATE TABLE vulkan_events (
			    id INTEGER PRIMARY KEY,
			    timestamp TIMESTAMP NOT NULL,
			    frame_number INTEGER NOT NULL,
			    function_name TEXT NOT NULL,
			    event_type TEXT,
			    memory_delta BIGINT,
			    parameters TEXT,
			    result_code INTEGER,
			    thread_id TEXT
			);
			CREATE SEQUENCE seq_vulkan_event_id START 1;

			-- Table for periodic memory usage snapshots:
			CREATE TABLE memory_usage (
			    id INTEGER PRIMARY KEY,
			    timestamp TIMESTAMP NOT NULL,
			    total_allocated BIGINT,
			    allocation_count INTEGER,
			    deallocation_count INTEGER
			);
			CREATE SEQUENCE seq_memory_usage_id START 1;
	)");

	if (queryResult && queryResult->HasError())
	{
		CCT_ASSERT_FALSE("Query failed with error: '{}'", queryResult->GetError());
	}
}

void* VulkanMemoryInspector::AllocationFunction(void* pUserData, size_t size, size_t alignment, VkSystemAllocationScope allocationScope)
{
	LowerAllocation* lowerAllocation = static_cast<LowerAllocation*>(pUserData);
	if (!lowerAllocation)
	{
		CCT_ASSERT_FALSE("Invalid pUserData pointer");
		return nullptr;
	}

	//if (lowerAllocation->allocationCallbacks && lowerAllocation->allocationCallbacks->pfnAllocation)
	//	return lowerAllocation->allocationCallbacks->pfnAllocation(pUserData, size, alignment, allocationScope);

	void* alloc = mi_malloc_aligned(size, alignment);
	if (!alloc)
	{
		CCT_ASSERT_FALSE("Could not allocate memory: size={}, alignment={}", size, alignment);
		return nullptr;
	}

	return alloc;
}

void* VulkanMemoryInspector::ReallocationFunction(void* pUserData, void* pOriginal, size_t size, size_t alignment, VkSystemAllocationScope allocationScope)
{
	LowerAllocation* lowerAllocation = static_cast<LowerAllocation*>(pUserData);
	if (!lowerAllocation)
	{
		CCT_ASSERT_FALSE("Invalid pUserData pointer");
		return nullptr;
	}

	if (lowerAllocation->allocationCallbacks && lowerAllocation->allocationCallbacks->pfnReallocation)
		return lowerAllocation->allocationCallbacks->pfnReallocation(pUserData, pOriginal, size, alignment, allocationScope);

	void* alloc = mi_realloc_aligned(pOriginal, size, alignment);
	if (!alloc)
	{
		CCT_ASSERT_FALSE("Could not allocate memory: size={}, alignment={}", size, alignment);
		return nullptr;
	}

	return alloc;
}

void VulkanMemoryInspector::FreeFunction(void* pUserData, void* pMemory)
{
	LowerAllocation* lowerAllocation = static_cast<LowerAllocation*>(pUserData);
	if (!lowerAllocation)
	{
		CCT_ASSERT_FALSE("Invalid pUserData pointer");
		return;
	}
	//if (lowerAllocation->allocationCallbacks && lowerAllocation->allocationCallbacks->pfnFree)
	//	return lowerAllocation->allocationCallbacks->pfnFree(pUserData, pMemory);
	mi_free(pMemory);
}

void VulkanMemoryInspector::InternalAllocationNotification(void* pUserData, size_t size, VkInternalAllocationType allocationType, VkSystemAllocationScope allocationScope)
{
	LowerAllocation* lowerAllocation = static_cast<LowerAllocation*>(pUserData);
	if (!lowerAllocation)
	{
		CCT_ASSERT_FALSE("Invalid pUserData pointer");
		return;
	}

	if (lowerAllocation->allocationCallbacks && lowerAllocation->allocationCallbacks->pfnInternalAllocation)
		return lowerAllocation->allocationCallbacks->pfnInternalAllocation(pUserData, size, allocationType, allocationScope);
}

void VulkanMemoryInspector::InternalFreeNotification(void* pUserData, size_t size, VkInternalAllocationType allocationType, VkSystemAllocationScope allocationScope)
{
	LowerAllocation* lowerAllocation = static_cast<LowerAllocation*>(pUserData);
	if (!lowerAllocation)
	{
		CCT_ASSERT_FALSE("Invalid pUserData pointer");
		return;
	}

	if (lowerAllocation->allocationCallbacks && lowerAllocation->allocationCallbacks->pfnInternalFree)
		return lowerAllocation->allocationCallbacks->pfnInternalFree(pUserData, size, allocationType, allocationScope);
}
