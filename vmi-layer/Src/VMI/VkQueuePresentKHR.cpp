//
// Created by arthur on 01/03/2025.
//

#include "VMI/Bindings.hpp"
#include "VMI/VulkanFunctions.hpp"
#include "VMI/VulkanMemoryInspector.hpp"

VkResult vkQueuePresentKHR(VkQueue queue, const VkPresentInfoKHR* pPresentInfo)
{
	const auto* dp = VulkanMemoryInspector::GetInstance()->GetDeviceDispatchTable(GetKey(queue));
	if (!dp)
	{
		CCT_ASSERT_FALSE("Could not get the device dispatch table");
		return VK_ERROR_INVALID_EXTERNAL_HANDLE;
	}

	VkResult result = dp->QueuePresentKHR(queue, pPresentInfo);

	FrameInformation frameInformation = {
		.frameIndex = VulkanMemoryInspector::GetInstance()->GetFrameIndex(),
		.startedAt = GetCurrentTimeStamp()
	};
	auto buff = Serialize(frameInformation);
	VulkanMemoryInspector::GetInstance()->Send(buff);
	VulkanMemoryInspector::GetInstance()->NextFrame();
	return result;
}