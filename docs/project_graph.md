# Project Architecture & Dependency Knowledge Graph

> **Generated automatically for Google Gemini and Graphify.**
> Maps every connected module node with zero token waste.

```mermaid
flowchart LR
    subgraph Core_Layer ["Core Architecture"]
        core_config["core/config"]
        core_event_bus["core/event_bus"]
        core_events["core/events"]
        core_input_keyboard["core/input_keyboard"]
        core_logger["core/logger"]
    end
    subgraph Vision_Pipeline ["Vision Pipeline"]
        vision_action_detector["vision/action_detector"]
        vision_camera_manager["vision/camera_manager"]
        vision_camera_supervisor["vision/camera_supervisor"]
        vision_debug_tools["vision/debug_tools"]
        vision_player_lock["vision/player_lock"]
        vision_pose_tracker["vision/pose_tracker"]
        vision_zone_calibration["vision/zone_calibration"]
    end
    subgraph Engine_Layer ["Engine & Controller"]
        engine_motion_bridge["engine/motion_bridge"]
        engine_tutorial_ui["engine/tutorial_ui"]
    end
    subgraph Tools_Layer ["Tools & Launchers"]
        tools_build_controller_exe["tools/build_controller_exe"]
        tools_calibrate_session["tools/calibrate_session"]
        tools_cam_probe["tools/cam_probe"]
        tools_generate_graph["tools/generate_graph"]
        tools_inspect_cameras["tools/inspect_cameras"]
        tools_show_tree["tools/show_tree"]
        tools_update_git_commits["tools/update_git_commits"]
    end

    %% Data Flow Connections
    core_config --> core_logger
    core_event_bus --> core_events
    core_event_bus --> core_logger
    core_input_keyboard --> core_config
    core_input_keyboard --> core_event_bus
    core_input_keyboard --> core_events
    core_input_keyboard --> core_logger
    engine_motion_bridge --> core_config
    engine_motion_bridge --> core_event_bus
    engine_motion_bridge --> core_events
    engine_motion_bridge --> core_logger
    engine_tutorial_ui --> core_events
    engine_tutorial_ui --> vision_pose_tracker
    tools_calibrate_session --> core_config
    tools_calibrate_session --> core_event_bus
    tools_calibrate_session --> core_events
    tools_calibrate_session --> core_logger
    tools_calibrate_session --> vision_action_detector
    tools_calibrate_session --> vision_camera_supervisor
    tools_calibrate_session --> vision_pose_tracker
    vision_action_detector --> core_config
    vision_action_detector --> core_event_bus
    vision_action_detector --> core_events
    vision_action_detector --> core_logger
    vision_action_detector --> vision_pose_tracker
    vision_camera_manager --> core_config
    vision_camera_manager --> core_event_bus
    vision_camera_manager --> core_events
    vision_camera_manager --> core_logger
    vision_camera_supervisor --> core_config
    vision_camera_supervisor --> core_event_bus
    vision_camera_supervisor --> core_events
    vision_camera_supervisor --> core_logger
    vision_camera_supervisor --> vision_camera_manager
    vision_debug_tools --> core_config
    vision_debug_tools --> core_event_bus
    vision_debug_tools --> core_events
    vision_debug_tools --> core_logger
    vision_player_lock --> core_config
    vision_player_lock --> core_event_bus
    vision_player_lock --> core_events
    vision_player_lock --> core_logger
    vision_player_lock --> vision_pose_tracker
    vision_player_lock --> vision_zone_calibration
    vision_pose_tracker --> core_config
    vision_pose_tracker --> core_event_bus
    vision_pose_tracker --> core_events
    vision_pose_tracker --> core_logger
    vision_zone_calibration --> core_config
    vision_zone_calibration --> core_event_bus
    vision_zone_calibration --> core_events
    vision_zone_calibration --> core_logger
    vision_zone_calibration --> vision_pose_tracker
```

---
Run `python tools/generate_graph.py` anytime code changes to refresh this graph!
