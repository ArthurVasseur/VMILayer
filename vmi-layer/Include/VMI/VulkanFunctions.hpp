//
// Created by arthur on 01/03/2025.
//

#ifndef GEI_VULKANFUNCTION_HPP
#define GEI_VULKANFUNCTION_HPP

#include <chrono>
#include <memory>
#include <thread>

#include "VMI/Defines.hpp"

#define VMI_CATCH_AND_RETURN(code, unhandledReturnValue, func)				\
		try																	\
		{																	\
			code;															\
		}																	\
		catch (const std::bad_alloc& e)										\
		{																	\
			if constexpr (std::is_void_v<decltype(func)>)					\
				return;														\
			else return VK_ERROR_OUT_OF_HOST_MEMORY;						\
		}																	\
		catch (const std::exception& e)										\
		{																	\
			std::cerr << "std::exception thrown: " << e.what() << '\n';		\
			if constexpr (std::is_void_v<decltype(func)>)					\
				return;														\
			else return unhandledReturnValue;								\
		}																	\
		catch (...)															\
		{																	\
			if constexpr (std::is_void_v<decltype(func)>)					\
				return;														\
			else return unhandledReturnValue;								\
		}


#define VMI_GET_ALLOCATION_CALLBACKS(variableName)										\
	auto variableName = VulkanMemoryInspector::GetInstance()->GetAllocationCallbacks();	\
	LowerAllocation lowerAllocation87 =													\
	{																					\
		.allocationCallbacks = pAllocator												\
	};																					\
	variableName.pUserData = static_cast<void*>(&lowerAllocation87)

//#define GEI_GET_KEY(ptr) *(void **)(ptr)
template<typename DispatchableType>
void* GetKey(DispatchableType inst)
{
	return *(void**)inst;
}

static cct::Int64 GetCurrentTimeStamp()
{
	using namespace std::chrono;
	auto now = system_clock::now();
	auto duration = now.time_since_epoch();
	return duration_cast<microseconds>(duration).count();
}

static cct::Int64 GetCurrentThreadId()
{
  auto id = std::this_thread::get_id();
	return std::hash<std::thread::id>()(id);
}

#endif //GEI_VULKANFUNCTION_HPP