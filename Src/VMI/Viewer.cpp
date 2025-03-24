//
// Created by arthur on 01/03/2025.
//

#include "VMI/Viewer.hpp"

#include <Concerto/Core/Assert.hpp>
#include <imgui.h>
#include <imgui_impl_sdl3.h>
#include <imgui_impl_sdlrenderer3.h>
#include <implot.h>

#include "VMI/VulkanFunctions.hpp"

namespace vmi
{
	Viewer::Viewer(duckdb::Connection db) :
		_window(nullptr),
		_renderer(nullptr),
		_db(std::move(db)),
		_shouldQuit(false),
		_startedAt(GetCurrentTimeStamp())
	{
	}

	Viewer::~Viewer()
	{
		ImGui_ImplSDLRenderer3_Shutdown();
		ImGui_ImplSDL3_Shutdown();
		ImPlot::DestroyContext();
		ImGui::DestroyContext();

		SDL_DestroyRenderer(_renderer);
		SDL_DestroyWindow(_window);
		SDL_Quit();
	}

	cct::Result<bool, std::string> Viewer::Create()
	{
		auto initFlags = SDL_WasInit(SDL_INIT_VIDEO);
		if ((initFlags & SDL_INIT_VIDEO) == 0)
		{
			auto res = SDL_Init(SDL_INIT_VIDEO);
			if (!res)
			{
				std::string error = std::format("Error: SDL_Init(): {}\n", SDL_GetError());
				CCT_ASSERT_FALSE("{}", error);
				return error;
			}
		}
		constexpr Uint32 windowFlags = SDL_WINDOW_RESIZABLE | SDL_WINDOW_HIDDEN;

		_window = SDL_CreateWindow("VMI - Viewer", 1280, 720, windowFlags);
		if (_window == nullptr)
		{
			std::string error = std::format("Error: SDL_CreateWindow(): {}\n", SDL_GetError());
			CCT_ASSERT_FALSE("{}", error);
			return error;
		}

		_renderer = SDL_CreateRenderer(_window, nullptr);
		SDL_SetRenderVSync(_renderer, 1);
		if (_renderer == nullptr)
		{
			std::string error = std::format("Error: SDL_CreateRenderer(): {}\n", SDL_GetError());
			CCT_ASSERT_FALSE("{}", error);
			return error;
		}

		SDL_SetWindowPosition(_window, SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED);
		SDL_ShowWindow(_window);

		IMGUI_CHECKVERSION();
		ImGui::CreateContext();
		ImPlot::CreateContext();
		ImGuiIO& io = ImGui::GetIO();
		io.ConfigFlags |= ImGuiConfigFlags_NavEnableKeyboard;     // Enable Keyboard Controls
		io.ConfigFlags |= ImGuiConfigFlags_NavEnableGamepad;      // Enable Gamepad Controls
		ImGui::StyleColorsDark();
		ImGui_ImplSDL3_InitForSDLRenderer(_window, _renderer);
		ImGui_ImplSDLRenderer3_Init(_renderer);

		return true;
	}

	void Viewer::Update()
	{
		ImVec4 clear_color = ImVec4(0.45f, 0.55f, 0.60f, 1.00f);
		ImGuiIO& io = ImGui::GetIO();

		SDL_Event event;
		while (SDL_PollEvent(&event))
		{
			ImGui_ImplSDL3_ProcessEvent(&event);
			if (event.type == SDL_EVENT_QUIT)
				_shouldQuit = true;
			if (event.type == SDL_EVENT_WINDOW_CLOSE_REQUESTED && event.window.windowID == SDL_GetWindowID(_window))
				_shouldQuit = true;
		}

		if (SDL_GetWindowFlags(_window) & SDL_WINDOW_MINIMIZED)
			return;

		ImGui_ImplSDLRenderer3_NewFrame();
		ImGui_ImplSDL3_NewFrame();
		std::vector<cct::Int32> timestamps;
		std::vector<cct::Int32> memoryUsed;

		// Run the SQL query.
		auto result = _db.Query("SELECT timestamp, memory_delta FROM vulkan_events ORDER BY timestamp ASC;");
		if (result->HasError())
		{
			std::cerr << "Query failed: " << result->GetError() << '\n';
			return;
		}

		std::unique_ptr<duckdb::DataChunk> chunk = result->Fetch();
		if (chunk)
		{
			for (size_t i = 0; i < chunk->size(); i++)
			{
				auto ts = chunk->GetValue(0, i).GetValue<duckdb::timestamp_t>();
				auto mem = chunk->GetValue(1, i).GetValue<cct::Int64>();
				timestamps.push_back((ts.value - _startedAt) / 1000);
				memoryUsed.push_back(mem / 8 / 1024);
			}
		}

		ImGui::NewFrame();
		{
			ImGui::Begin("Hello, world!");
			ImGui::Text("Application average %.3f ms/frame (%.1f FPS)", 1000.0f / io.Framerate, io.Framerate);
			if (!timestamps.empty() && ImPlot::BeginPlot("Real-time Memory Consumption"))
			{
				ImPlot::SetupAxes("Time (s)", "Memory Used (bytes)");
				if (!timestamps.empty() && timestamps.size() == memoryUsed.size())
				{
					// PlotShaded fills the area between the curve and the baseline (here, y = 0).
					//ImPlot::PlotShaded("Memory Used",
					//	timestamps.data(),
					//	memoryUsed.data(),
					//	static_cast<int>(timestamps.size()),
					//	0,       // offset (starting index)
					//	0.0,     // baseline y_ref
					//	ImPlotShadedFlags_None);
					ImPlot::PushStyleVar(ImPlotStyleVar_FillAlpha, 0.25f);
					ImPlot::PlotShaded("Memory Used", timestamps.data(), memoryUsed.data(), memoryUsed.size(), 0, 0, 0);
					ImPlot::PopStyleVar();
					ImPlot::EndPlot();
				}
				ImGui::End();
			}
			ImGui::Render();
			//SDL_RenderSetScale(renderer, io.DisplayFramebufferScale.x, io.DisplayFramebufferScale.y);
			SDL_SetRenderDrawColorFloat(_renderer, clear_color.x, clear_color.y, clear_color.z, clear_color.w);
			SDL_RenderClear(_renderer);
			ImGui_ImplSDLRenderer3_RenderDrawData(ImGui::GetDrawData(), _renderer);
			SDL_RenderPresent(_renderer);
		}
	}
}
