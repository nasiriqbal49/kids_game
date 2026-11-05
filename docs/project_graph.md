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
        engine_audio["engine/audio"]
        engine_display["engine/display"]
        engine_event_pump["engine/event_pump"]
        engine_game_engine["engine/game_engine"]
        engine_mechanics_entities["engine/mechanics/entities"]
        engine_mechanics_manager["engine/mechanics/manager"]
        engine_motion_bridge["engine/motion_bridge"]
        engine_tutorial_ui["engine/tutorial_ui"]
    end
    subgraph Identity_Layer ["Identity & Economy"]
        identity_measurement_capture["identity/measurement_capture"]
        identity_profile_manager["identity/profile_manager"]
        identity_shop_manager["identity/shop_manager"]
    end
    subgraph Projection_Layer ["Projection Output"]
        projection_projector_manager["projection/projector_manager"]
    end
    subgraph Tools_Layer ["Tools & Launchers"]
        tools_build_controller_exe["tools/build_controller_exe"]
        tools_build_exe["tools/build_exe"]
        tools_calibrate_session["tools/calibrate_session"]
        tools_extract_module["tools/extract_module"]
        tools_generate_graph["tools/generate_graph"]
        tools_inspect_cameras["tools/inspect_cameras"]
        tools_make_session_diff["tools/make_session_diff"]
        tools_motion_controller_app["tools/motion_controller_app"]
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
    engine_audio --> core_config
    engine_audio --> core_event_bus
    engine_audio --> core_events
    engine_audio --> core_logger
    engine_display --> core_config
    engine_display --> core_event_bus
    engine_display --> core_events
    engine_display --> core_logger
    engine_event_pump --> core_logger
    engine_game_engine --> core_config
    engine_game_engine --> core_event_bus
    engine_game_engine --> core_events
    engine_game_engine --> core_logger
    engine_mechanics_manager --> core_config
    engine_mechanics_manager --> core_event_bus
    engine_mechanics_manager --> core_events
    engine_mechanics_manager --> core_logger
    engine_mechanics_manager --> engine_mechanics_entities
    engine_motion_bridge --> core_config
    engine_motion_bridge --> core_event_bus
    engine_motion_bridge --> core_events
    engine_motion_bridge --> core_logger
    engine_tutorial_ui --> core_events
    engine_tutorial_ui --> vision_pose_tracker
    identity_measurement_capture --> core_config
    identity_measurement_capture --> core_event_bus
    identity_measurement_capture --> core_events
    identity_measurement_capture --> core_logger
    identity_measurement_capture --> identity_profile_manager
    identity_measurement_capture --> vision_pose_tracker
    identity_profile_manager --> core_config
    identity_profile_manager --> core_event_bus
    identity_profile_manager --> core_events
    identity_profile_manager --> core_logger
    identity_shop_manager --> core_config
    identity_shop_manager --> core_event_bus
    identity_shop_manager --> core_events
    identity_shop_manager --> core_logger
    identity_shop_manager --> identity_profile_manager
    projection_projector_manager --> core_config
    projection_projector_manager --> core_event_bus
    projection_projector_manager --> core_events
    projection_projector_manager --> core_logger
    tools_calibrate_session --> core_config
    tools_calibrate_session --> core_event_bus
    tools_calibrate_session --> core_events
    tools_calibrate_session --> core_logger
    tools_calibrate_session --> vision_action_detector
    tools_calibrate_session --> vision_camera_supervisor
    tools_calibrate_session --> vision_pose_tracker
    tools_motion_controller_app --> core_config
    tools_motion_controller_app --> core_event_bus
    tools_motion_controller_app --> core_logger
    tools_motion_controller_app --> engine_motion_bridge
    tools_motion_controller_app --> engine_tutorial_ui
    tools_motion_controller_app --> vision_action_detector
    tools_motion_controller_app --> vision_camera_supervisor
    tools_motion_controller_app --> vision_player_lock
    tools_motion_controller_app --> vision_pose_tracker
    tools_motion_controller_app --> vision_zone_calibration
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
