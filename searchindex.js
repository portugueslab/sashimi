Search.setIndex({docnames:["configuration","development/code_organization","hardware","index","intro","modules","sashimi","sashimi.gui","sashimi.hardware","sashimi.hardware.scanning","sashimi.processes"],envversion:{"sphinx.domains.c":2,"sphinx.domains.changeset":1,"sphinx.domains.citation":1,"sphinx.domains.cpp":2,"sphinx.domains.index":1,"sphinx.domains.javascript":2,"sphinx.domains.math":2,"sphinx.domains.python":2,"sphinx.domains.rst":2,"sphinx.domains.std":1,sphinx:56},filenames:["configuration.md","development/code_organization.md","hardware.md","index.md","intro.md","modules.rst","sashimi.rst","sashimi.gui.rst","sashimi.hardware.rst","sashimi.hardware.scanning.rst","sashimi.processes.rst"],objects:{"":{sashimi:[6,0,0,"-"]},"sashimi.camera":{CamParameters:[6,1,1,""],CameraMode:[6,1,1,""],CameraProcess:[6,1,1,""],FramerateRecorder:[6,1,1,""],MockCameraProcess:[6,1,1,""],TriggerMode:[6,1,1,""]},"sashimi.camera.CamParameters":{binning:[6,2,1,""],camera_mode:[6,2,1,""],exposure_time:[6,2,1,""],frame_shape:[6,2,1,""],image_height:[6,2,1,""],image_width:[6,2,1,""],internal_frame_rate:[6,2,1,""],subarray:[6,2,1,""],trigger_mode:[6,2,1,""]},"sashimi.camera.CameraMode":{ABORT:[6,2,1,""],EXPERIMENT_RUNNING:[6,2,1,""],PAUSED:[6,2,1,""],PREVIEW:[6,2,1,""],TRIGGERED:[6,2,1,""]},"sashimi.camera.CameraProcess":{apply_parameters:[6,3,1,""],camera_loop:[6,3,1,""],cast_parameters:[6,3,1,""],close_camera:[6,3,1,""],initialize_camera:[6,3,1,""],pause_loop:[6,3,1,""],run:[6,3,1,""],run_camera:[6,3,1,""],update_framerate:[6,3,1,""]},"sashimi.camera.FramerateRecorder":{update_framerate:[6,3,1,""]},"sashimi.camera.MockCameraProcess":{apply_parameters:[6,3,1,""],camera_loop:[6,3,1,""],cast_parameters:[6,3,1,""],close_camera:[6,3,1,""],initialize_camera:[6,3,1,""],pause_loop:[6,3,1,""],run:[6,3,1,""],run_camera:[6,3,1,""],update_framerate:[6,3,1,""]},"sashimi.camera.TriggerMode":{EXTERNAL_TRIGGER:[6,2,1,""],FREE:[6,2,1,""]},"sashimi.config":{cli_edit_config:[6,4,1,""],read_config:[6,4,1,""],write_config_value:[6,4,1,""],write_default_config:[6,4,1,""]},"sashimi.events":{AutoName:[6,1,1,""],LoggedEvent:[6,1,1,""],SashimiEvents:[6,1,1,""]},"sashimi.events.LoggedEvent":{clear:[6,3,1,""],is_set:[6,3,1,""],new_reference:[6,3,1,""],set:[6,3,1,""]},"sashimi.events.SashimiEvents":{CLOSE_ALL:[6,2,1,""],IS_SAVING:[6,2,1,""],NOISE_SUBTRACTION_ACTIVE:[6,2,1,""],RESTART_SCANNING:[6,2,1,""],SAVING_STOPPED:[6,2,1,""],TRIGGER_STYTRA:[6,2,1,""],WAITING_FOR_TRIGGER:[6,2,1,""]},"sashimi.gui":{calibration_gui:[7,0,0,"-"],camera_gui:[7,0,0,"-"],laser_gui:[7,0,0,"-"],main_gui:[7,0,0,"-"],save_gui:[7,0,0,"-"],save_settings_gui:[7,0,0,"-"],scanning_gui:[7,0,0,"-"],waveform_gui:[7,0,0,"-"]},"sashimi.gui.calibration_gui":{CalibrationWidget:[7,1,1,""],NoiseSubtractionSettings:[7,1,1,""]},"sashimi.gui.calibration_gui.CalibrationWidget":{perform_noise_subtraction:[7,3,1,""],refresh_widgets:[7,3,1,""],set_noise_subtraction_mode:[7,3,1,""],show_dialog_box:[7,3,1,""],update_label:[7,3,1,""]},"sashimi.gui.camera_gui":{CameraSettingsContainerWidget:[7,1,1,""],DisplaySettings:[7,1,1,""],ViewingWidget:[7,1,1,""]},"sashimi.gui.camera_gui.CameraSettingsContainerWidget":{roi_pos:[7,3,1,""],roi_size:[7,3,1,""],set_full_size_frame:[7,3,1,""],set_roi:[7,3,1,""],update_camera_info:[7,3,1,""],update_roi_info:[7,3,1,""]},"sashimi.gui.camera_gui.ViewingWidget":{refresh:[7,3,1,""],refresh_image:[7,3,1,""],refresh_progress_bar:[7,3,1,""],toggle_roi_display:[7,3,1,""],update_contrast_limits:[7,3,1,""],update_roi:[7,3,1,""],voxel_size:[7,3,1,""]},"sashimi.gui.laser_gui":{LaserControlWidget:[7,1,1,""]},"sashimi.gui.laser_gui.LaserControlWidget":{toggle:[7,3,1,""],update_current:[7,3,1,""]},"sashimi.gui.main_gui":{DockedWidget:[7,1,1,""],MainWindow:[7,1,1,""],PausedWidget:[7,1,1,""],StatusWidget:[7,1,1,""]},"sashimi.gui.main_gui.MainWindow":{check_end_experiment:[7,3,1,""],closeEvent:[7,3,1,""],refresh_param_values:[7,3,1,""]},"sashimi.gui.main_gui.StatusWidget":{update_status:[7,3,1,""]},"sashimi.gui.save_gui":{SaveWidget:[7,1,1,""]},"sashimi.gui.save_gui.SaveWidget":{set_locationbutton:[7,3,1,""],set_save_location:[7,3,1,""]},"sashimi.gui.save_settings_gui":{SavingSettingsWidget:[7,1,1,""]},"sashimi.gui.save_settings_gui.SavingSettingsWidget":{load:[7,3,1,""],save:[7,3,1,""],sig_params_loaded:[7,2,1,""]},"sashimi.gui.scanning_gui":{PlanarScanningWidget:[7,1,1,""],SinglePlaneScanningWidget:[7,1,1,""],VolumeScanningWidget:[7,1,1,""]},"sashimi.gui.scanning_gui.VolumeScanningWidget":{change_experiment_state:[7,3,1,""],change_pause_status:[7,3,1,""],overwrite_alert_popup:[7,3,1,""],updateBtnText:[7,3,1,""],update_alignment:[7,3,1,""]},"sashimi.gui.waveform_gui":{WaveformWidget:[7,1,1,""]},"sashimi.gui.waveform_gui.WaveformWidget":{update:[7,3,1,""],update_pulses:[7,3,1,""]},"sashimi.hardware":{hamamatsu_camera:[8,0,0,"-"],laser:[8,0,0,"-"],scanning:[9,0,0,"-"]},"sashimi.hardware.hamamatsu_camera":{DCAMAPI_INIT:[8,1,1,""],DCAMBUF_ATTACH:[8,1,1,""],DCAMBUF_FRAME:[8,1,1,""],DCAMCAP_TRANSFERINFO:[8,1,1,""],DCAMDEV_OPEN:[8,1,1,""],DCAMDEV_STRING:[8,1,1,""],DCAMException:[8,5,1,""],DCAMPROP_ATTR:[8,1,1,""],DCAMPROP_VALUETEXT:[8,1,1,""],DCAMWAIT_OPEN:[8,1,1,""],DCAMWAIT_START:[8,1,1,""],DCamAPI:[8,1,1,""],HCamData:[8,1,1,""],HamamatsuCamera:[8,1,1,""],HamamatsuCameraMR:[8,1,1,""],convertPropertyName:[8,4,1,""]},"sashimi.hardware.hamamatsu_camera.DCAMAPI_INIT":{guid:[8,2,1,""],iDeviceCount:[8,2,1,""],initoption:[8,2,1,""],initoptionbytes:[8,2,1,""],reserved:[8,2,1,""],size:[8,2,1,""]},"sashimi.hardware.hamamatsu_camera.DCAMBUF_ATTACH":{buffer:[8,2,1,""],buffercount:[8,2,1,""],iKind:[8,2,1,""],size:[8,2,1,""]},"sashimi.hardware.hamamatsu_camera.DCAMBUF_FRAME":{buf:[8,2,1,""],camerastamp:[8,2,1,""],framestamp:[8,2,1,""],height:[8,2,1,""],iFrame:[8,2,1,""],iKind:[8,2,1,""],left:[8,2,1,""],option:[8,2,1,""],rowbytes:[8,2,1,""],size:[8,2,1,""],timestamp:[8,2,1,""],top:[8,2,1,""],type:[8,2,1,""],width:[8,2,1,""]},"sashimi.hardware.hamamatsu_camera.DCAMCAP_TRANSFERINFO":{iKind:[8,2,1,""],nFrameCount:[8,2,1,""],nNewestFrameIndex:[8,2,1,""],size:[8,2,1,""]},"sashimi.hardware.hamamatsu_camera.DCAMDEV_OPEN":{hdcam:[8,2,1,""],index:[8,2,1,""],size:[8,2,1,""]},"sashimi.hardware.hamamatsu_camera.DCAMDEV_STRING":{iString:[8,2,1,""],size:[8,2,1,""],text:[8,2,1,""],textbytes:[8,2,1,""]},"sashimi.hardware.hamamatsu_camera.DCAMPROP_ATTR":{attribute2:[8,2,1,""],attribute:[8,2,1,""],cbSize:[8,2,1,""],iGroup:[8,2,1,""],iProp:[8,2,1,""],iPropStep_Element:[8,2,1,""],iProp_ArrayBase:[8,2,1,""],iProp_NumberOfElement:[8,2,1,""],iReserved1:[8,2,1,""],iReserved3:[8,2,1,""],iUnit:[8,2,1,""],nMaxChannel:[8,2,1,""],nMaxView:[8,2,1,""],option:[8,2,1,""],valuedefault:[8,2,1,""],valuemax:[8,2,1,""],valuemin:[8,2,1,""],valuestep:[8,2,1,""]},"sashimi.hardware.hamamatsu_camera.DCAMPROP_VALUETEXT":{cbSize:[8,2,1,""],iProp:[8,2,1,""],text:[8,2,1,""],textbytes:[8,2,1,""],value:[8,2,1,""]},"sashimi.hardware.hamamatsu_camera.DCAMWAIT_OPEN":{hdcam:[8,2,1,""],hwait:[8,2,1,""],size:[8,2,1,""],supportevent:[8,2,1,""]},"sashimi.hardware.hamamatsu_camera.DCAMWAIT_START":{eventhappened:[8,2,1,""],eventmask:[8,2,1,""],size:[8,2,1,""],timeout:[8,2,1,""]},"sashimi.hardware.hamamatsu_camera.HCamData":{copyData:[8,3,1,""],getData:[8,3,1,""],getDataPtr:[8,3,1,""]},"sashimi.hardware.hamamatsu_camera.HamamatsuCamera":{captureSetup:[8,3,1,""],checkStatus:[8,3,1,""],exposure:[8,3,1,""],getCameraProperties:[8,3,1,""],getFrames:[8,3,1,""],getModelInfo:[8,3,1,""],getProperties:[8,3,1,""],getPropertyAttribute:[8,3,1,""],getPropertyRW:[8,3,1,""],getPropertyRange:[8,3,1,""],getPropertyText:[8,3,1,""],getPropertyValue:[8,3,1,""],isCameraProperty:[8,3,1,""],newFrames:[8,3,1,""],setACQMode:[8,3,1,""],setPropertyValue:[8,3,1,""],setSubArrayMode:[8,3,1,""],shutdown:[8,3,1,""],sortedPropertyTextOptions:[8,3,1,""],startAcquisition:[8,3,1,""],stopAcquisition:[8,3,1,""]},"sashimi.hardware.hamamatsu_camera.HamamatsuCameraMR":{getFrames:[8,3,1,""],startAcquisition:[8,3,1,""],stopAcquisition:[8,3,1,""]},"sashimi.hardware.laser":{CoboltLaser:[8,1,1,""],MockCoboltLaser:[8,1,1,""]},"sashimi.hardware.laser.CoboltLaser":{close:[8,3,1,""],get_status:[8,3,1,""],set_current:[8,3,1,""]},"sashimi.hardware.laser.MockCoboltLaser":{close:[8,3,1,""],get_status:[8,3,1,""],set_current:[8,3,1,""]},"sashimi.hardware.scanning":{"interface":[9,0,0,"-"],mock:[9,0,0,"-"],ni:[9,0,0,"-"],scanloops:[9,0,0,"-"]},"sashimi.hardware.scanning.interface":{AbstractScanInterface:[9,1,1,""],ScanningError:[9,5,1,""],open_abstract_interface:[9,4,1,""]},"sashimi.hardware.scanning.interface.AbstractScanInterface":{camera_trigger:[9,3,1,""],read:[9,3,1,""],start:[9,3,1,""],write:[9,3,1,""],xy_frontal:[9,3,1,""],xy_lateral:[9,3,1,""],z_frontal:[9,3,1,""],z_lateral:[9,3,1,""],z_piezo:[9,3,1,""]},"sashimi.hardware.scanning.mock":{MockBoard:[9,1,1,""],open_mockboard:[9,4,1,""]},"sashimi.hardware.scanning.mock.MockBoard":{z_piezo:[9,3,1,""]},"sashimi.hardware.scanning.ni":{NIBoards:[9,1,1,""],open_niboard:[9,4,1,""]},"sashimi.hardware.scanning.ni.NIBoards":{camera_trigger:[9,3,1,""],read:[9,3,1,""],setup_tasks:[9,3,1,""],start:[9,3,1,""],write:[9,3,1,""],xy_frontal:[9,3,1,""],xy_lateral:[9,3,1,""],z_frontal:[9,3,1,""],z_lateral:[9,3,1,""],z_piezo:[9,3,1,""]},"sashimi.hardware.scanning.scanloops":{ExperimentPrepareState:[9,1,1,""],PlanarScanLoop:[9,1,1,""],PlanarScanning:[9,1,1,""],ScanLoop:[9,1,1,""],ScanParameters:[9,1,1,""],ScanningState:[9,1,1,""],TriggeringParameters:[9,1,1,""],VolumetricScanLoop:[9,1,1,""],XYScanning:[9,1,1,""],ZManual:[9,1,1,""],ZScanning:[9,1,1,""],ZSynced:[9,1,1,""],calc_sync:[9,4,1,""]},"sashimi.hardware.scanning.scanloops.ExperimentPrepareState":{ABORT:[9,2,1,""],EXPERIMENT_STARTED:[9,2,1,""],NO_TRIGGER:[9,2,1,""],PREVIEW:[9,2,1,""]},"sashimi.hardware.scanning.scanloops.PlanarScanLoop":{fill_arrays:[9,3,1,""],loop_condition:[9,3,1,""],n_samples_period:[9,3,1,""]},"sashimi.hardware.scanning.scanloops.PlanarScanning":{frontal:[9,2,1,""],lateral:[9,2,1,""]},"sashimi.hardware.scanning.scanloops.ScanLoop":{check_start:[9,3,1,""],fill_arrays:[9,3,1,""],initialize:[9,3,1,""],loop:[9,3,1,""],loop_condition:[9,3,1,""],n_samples_period:[9,3,1,""],read:[9,3,1,""],update_settings:[9,3,1,""],write:[9,3,1,""]},"sashimi.hardware.scanning.scanloops.ScanParameters":{experiment_state:[9,2,1,""],state:[9,2,1,""],triggering:[9,2,1,""],xy:[9,2,1,""],z:[9,2,1,""]},"sashimi.hardware.scanning.scanloops.ScanningState":{PAUSED:[9,2,1,""],PLANAR:[9,2,1,""],VOLUMETRIC:[9,2,1,""]},"sashimi.hardware.scanning.scanloops.TriggeringParameters":{frequency:[9,2,1,""],n_planes:[9,2,1,""],n_skip_end:[9,2,1,""],n_skip_start:[9,2,1,""]},"sashimi.hardware.scanning.scanloops.VolumetricScanLoop":{check_start:[9,3,1,""],fill_arrays:[9,3,1,""],initialize:[9,3,1,""],loop_condition:[9,3,1,""],n_samples_period:[9,3,1,""],read:[9,3,1,""],update_settings:[9,3,1,""]},"sashimi.hardware.scanning.scanloops.XYScanning":{frequency:[9,2,1,""],vmax:[9,2,1,""],vmin:[9,2,1,""]},"sashimi.hardware.scanning.scanloops.ZManual":{frontal:[9,2,1,""],lateral:[9,2,1,""],piezo:[9,2,1,""]},"sashimi.hardware.scanning.scanloops.ZScanning":{frequency:[9,2,1,""],frontal_sync:[9,2,1,""],lateral_sync:[9,2,1,""],piezo_max:[9,2,1,""],piezo_min:[9,2,1,""]},"sashimi.hardware.scanning.scanloops.ZSynced":{frontal_sync:[9,2,1,""],lateral_sync:[9,2,1,""],piezo:[9,2,1,""]},"sashimi.processes":{dispatcher:[10,0,0,"-"],logging:[10,0,0,"-"],scanning:[10,0,0,"-"],streaming_save:[10,0,0,"-"],stytra_comm:[10,0,0,"-"]},"sashimi.processes.dispatcher":{VolumeDispatcher:[10,1,1,""]},"sashimi.processes.dispatcher.VolumeDispatcher":{fill_queues:[10,3,1,""],get_frame:[10,3,1,""],process_frame:[10,3,1,""],reset:[10,3,1,""],run:[10,3,1,""],send_receive:[10,3,1,""]},"sashimi.processes.logging":{ConcurrenceLogger:[10,1,1,""],LoggingProcess:[10,1,1,""]},"sashimi.processes.logging.ConcurrenceLogger":{close:[10,3,1,""],log_event:[10,3,1,""],log_message:[10,3,1,""],log_queue:[10,3,1,""],write_entry:[10,3,1,""]},"sashimi.processes.logging.LoggingProcess":{close_log:[10,3,1,""]},"sashimi.processes.scanning":{Scanner:[10,1,1,""]},"sashimi.processes.scanning.Scanner":{retrieve_parameters:[10,3,1,""],run:[10,3,1,""]},"sashimi.processes.streaming_save":{SavingParameters:[10,1,1,""],SavingStatus:[10,1,1,""],StackSaver:[10,1,1,""]},"sashimi.processes.streaming_save.SavingParameters":{chunk_size:[10,2,1,""],n_planes:[10,2,1,""],n_volumes:[10,2,1,""],notification_email:[10,2,1,""],optimal_chunk_MB_RAM:[10,2,1,""],output_dir:[10,2,1,""],volumerate:[10,2,1,""],voxel_size:[10,2,1,""]},"sashimi.processes.streaming_save.SavingStatus":{i_chunk:[10,2,1,""],i_in_chunk:[10,2,1,""],i_volume:[10,2,1,""],target_params:[10,2,1,""]},"sashimi.processes.streaming_save.StackSaver":{calculate_optimal_size:[10,3,1,""],fill_dataset:[10,3,1,""],finalize_dataset:[10,3,1,""],receive_save_parameters:[10,3,1,""],run:[10,3,1,""],save_chunk:[10,3,1,""],save_loop:[10,3,1,""],update_saved_status_queue:[10,3,1,""]},"sashimi.processes.stytra_comm":{AbstractComm:[10,1,1,""],ExternalComm:[10,1,1,""],StytraComm:[10,1,1,""],clean_json:[10,4,1,""]},"sashimi.processes.stytra_comm.AbstractComm":{trigger_and_receive_duration:[10,3,1,""]},"sashimi.processes.stytra_comm.ExternalComm":{run:[10,3,1,""],trigger_condition:[10,3,1,""]},"sashimi.processes.stytra_comm.StytraComm":{trigger_and_receive_duration:[10,3,1,""]},"sashimi.rolling_buffer":{FillingRollingBuffer:[6,1,1,""],RollingBuffer:[6,1,1,""],fill_circular:[6,4,1,""],read_circular:[6,4,1,""],write_circular:[6,4,1,""]},"sashimi.rolling_buffer.FillingRollingBuffer":{is_complete:[6,3,1,""],write:[6,3,1,""]},"sashimi.rolling_buffer.RollingBuffer":{read:[6,3,1,""],write:[6,3,1,""]},"sashimi.state":{Calibration:[6,1,1,""],CalibrationZSettings:[6,1,1,""],CameraSettings:[6,1,1,""],GlobalState:[6,1,1,""],LaserSettings:[6,1,1,""],PlanarScanningSettings:[6,1,1,""],SaveSettings:[6,1,1,""],ScanningSettings:[6,1,1,""],ScopeAlignmentInfo:[6,1,1,""],SinglePlaneSettings:[6,1,1,""],State:[6,1,1,""],ZRecordingSettings:[6,1,1,""],convert_calibration_params:[6,4,1,""],convert_camera_params:[6,4,1,""],convert_planar_params:[6,4,1,""],convert_save_params:[6,4,1,""],convert_single_plane_params:[6,4,1,""],convert_volume_params:[6,4,1,""],get_voxel_size:[6,4,1,""]},"sashimi.state.Calibration":{add_calibration_point:[6,3,1,""],calculate_calibration:[6,3,1,""],remove_calibration_point:[6,3,1,""]},"sashimi.state.GlobalState":{EXPERIMENT_RUNNING:[6,2,1,""],PAUSED:[6,2,1,""],PLANAR_PREVIEW:[6,2,1,""],PREVIEW:[6,2,1,""],VOLUME_PREVIEW:[6,2,1,""]},"sashimi.state.State":{calculate_pulse_times:[6,3,1,""],change_global_state:[6,3,1,""],end_experiment:[6,3,1,""],get_camera_status:[6,3,1,""],get_save_status:[6,3,1,""],get_triggered_frame_rate:[6,3,1,""],get_volume:[6,3,1,""],get_waveform:[6,3,1,""],obtain_noise_average:[6,3,1,""],reset_noise_subtraction:[6,3,1,""],restore_tree:[6,3,1,""],save_tree:[6,3,1,""],send_camera_settings:[6,3,1,""],send_dispatcher_settings:[6,3,1,""],send_scan_settings:[6,3,1,""],start_experiment:[6,3,1,""],wrap_up:[6,3,1,""]},"sashimi.utilities":{get_last_parameters:[6,4,1,""],lcm:[6,4,1,""]},"sashimi.waveforms":{ConstantWaveform:[6,1,1,""],RecordedWaveform:[6,1,1,""],SawtoothWaveform:[6,1,1,""],TriangleWaveform:[6,1,1,""],Waveform:[6,1,1,""],set_impulses:[6,4,1,""]},"sashimi.waveforms.ConstantWaveform":{values:[6,3,1,""]},"sashimi.waveforms.RecordedWaveform":{values:[6,3,1,""]},"sashimi.waveforms.SawtoothWaveform":{values:[6,3,1,""]},"sashimi.waveforms.TriangleWaveform":{values:[6,3,1,""]},"sashimi.waveforms.Waveform":{values:[6,3,1,""]},sashimi:{camera:[6,0,0,"-"],config:[6,0,0,"-"],events:[6,0,0,"-"],gui:[7,0,0,"-"],hardware:[8,0,0,"-"],main:[6,0,0,"-"],processes:[10,0,0,"-"],rolling_buffer:[6,0,0,"-"],state:[6,0,0,"-"],utilities:[6,0,0,"-"],waveforms:[6,0,0,"-"]}},objnames:{"0":["py","module","Python module"],"1":["py","class","Python class"],"2":["py","attribute","Python attribute"],"3":["py","method","Python method"],"4":["py","function","Python function"],"5":["py","exception","Python exception"]},objtypes:{"0":"py:module","1":"py:class","2":"py:attribute","3":"py:method","4":"py:function","5":"py:exception"},terms:{"2gb":8,"class":[6,7,8,9,10],"default":7,"enum":[6,9,10],"float":[6,9,10],"function":[1,6,8],"int":[6,7,9,10],"new":[3,6,8],"return":[6,8],"throw":8,"true":[7,10],"try":8,"while":4,Are:8,For:[1,4],The:[4,8],Then:4,There:8,Use:8,Uses:8,Using:8,_ctype:8,abort:[6,8,9],abov:4,abstractcomm:10,abstractscaninterfac:9,access:8,acquir:[6,8],acquisit:[4,8],activ:4,add:4,add_calibration_point:6,added:1,address:8,admonit:4,after:8,ahem:1,ai0:6,all:[4,8],alloc:8,allow:[4,8],alreadi:8,also:8,altern:3,alwai:8,anaconda:4,ani:[4,8],anywai:8,ao0:[4,6],api:3,apply_paramet:6,appropri:8,architectur:4,arg:[6,8,9,10],arr:6,arrai:[6,8],array_ram_mb:6,arrayqueu:[9,10],ask:4,associ:8,attribut:8,attribute2:8,autonam:6,avail:8,averag:6,avoid:8,badli:8,bar:7,base:[6,7,8,9,10],basecontext:[6,10],basic:8,beam:2,begin:8,behind:8,believ:8,bin:6,bit:8,block:8,board:[1,4,9],bool:10,both:6,bottleneck:8,brain:2,buf:8,buffer:[6,8],buffercount:8,built:[2,4],c_int32:8,c_int:8,calc_sync:9,calcul:6,calculate_calibr:6,calculate_optimal_s:10,calculate_pulse_tim:6,calibr:[6,7],calibration_gui:[5,6],calibration_st:7,calibrationwidget:7,calibrationzset:6,call:[7,8],camera:[1,4,5,7,8],camera_gui:[5,6],camera_id:[6,8],camera_loop:6,camera_mod:6,camera_queu:10,camera_set:6,camera_trigg:9,cameramod:6,cameraprocess:6,cameraset:6,camerasettingscontainerwidget:7,camerastamp:8,camparamet:6,can:[4,6,8,10],captur:8,capturesetup:8,cast_paramet:6,cbsize:8,central:7,change_experiment_st:7,change_global_st:6,change_pause_statu:7,channel:[4,6],chao:8,check:8,check_end_experi:7,check_start:9,checkstatu:8,chunk_siz:10,circular:6,clash:8,clean_json:10,clear:6,cli_edit_config:6,clone:4,close:[8,10],close_al:6,close_camera:6,close_log:10,closeev:7,coboltlas:[7,8],code:8,com4:8,command:3,common:6,compar:8,computer_adderss:10,concurrencelogg:[9,10],conda:4,condit:8,conf:9,config:[4,5,10],configpars:6,configur:[3,6,8],confus:[6,8],connect:[4,8],constant_valu:6,constantwaveform:6,content:[4,5],context:[6,10],contribut:4,control:[1,4,8],convert_calibration_param:6,convert_camera_param:6,convert_planar_param:6,convert_save_param:6,convert_single_plane_param:6,convert_volume_param:6,convertpropertynam:8,copi:8,copydata:8,could:8,count:8,creat:3,create_string_buff:8,ctype:8,current:[4,8],data:[6,8],dcam:8,dcamapi:8,dcamapi_init:8,dcambuf_attach:8,dcambuf_fram:8,dcamcap_transferinfo:8,dcamdev_open:8,dcamdev_str:8,dcamexcept:8,dcamprop_attr:8,dcamprop_valuetext:8,dcamwait_open:8,dcamwait_start:8,deactiv:7,debug:4,default_path:6,defin:1,depend:4,determin:8,dev1:[4,6],dev2:6,develop:4,dict:6,dict_path:6,digit:[2,4],directli:6,dispatch:[5,6],displai:[4,6,7],displayset:7,distribut:4,dockedwidget:7,document:8,doe:8,don:6,down:8,downstream:8,drive:4,drop:8,drosophila:2,dslm:4,dtype:6,duration_queu:10,dynam:8,each:[1,8],easi:4,edit:4,effici:4,either:8,element:8,empti:8,end:8,end_experi:6,entiti:1,enumer:[6,9],env:4,environ:3,error:8,even:8,event:[5,10],event_id:10,event_nam:10,event_typ:10,event_valu:10,eventhappen:8,eventmask:8,everi:[4,6],exampl:4,except:[8,9],exp_trigger_ev:6,expect:[1,8],experi:4,experiment_run:6,experiment_st:9,experiment_start:9,experiment_start_ev:10,experimentpreparest:9,explicitli:8,exposur:8,exposure_tim:6,external_trigg:6,externalcomm:10,fall:8,fals:[6,7,8,9,10],fast:4,file:6,file_path:6,fill:6,fill_arrai:9,fill_circular:6,fill_dataset:10,fill_queu:10,fillingrollingbuff:6,finalize_dataset:10,finish:7,first:6,first_run:9,fit:8,fix:8,fixed_length:8,fixm:8,flash:8,fn_name:8,fn_return:8,folder:4,found:4,frame:[6,8],frame_shap:6,framer:6,frameraterecord:6,framestamp:8,free:6,frequenc:[6,9],friendli:4,from:[3,6,7,8],frontal:9,frontal_sync:9,full:6,georg:8,get:8,get_camera_statu:6,get_fram:10,get_last_paramet:6,get_save_statu:6,get_statu:8,get_triggered_frame_r:6,get_volum:6,get_voxel_s:6,get_waveform:6,getcameraproperti:8,getdata:8,getdataptr:8,getfram:8,getmodelinfo:8,getproperti:8,getpropertyattribut:8,getpropertyrang:8,getpropertyrw:8,getpropertytext:8,getpropertyvalu:8,give:1,globalst:6,good:4,gui:[5,6],guid:[4,8],hamamatsu:8,hamamatsu_camera:[5,6],hamamatsucamera:8,hamamatsucameramr:8,hardwar:[1,3,4,5,6,7],hardware_config:6,has:8,hazen:8,hcamdata:8,hdcam:8,height:8,help:4,here:[3,8],high:6,home:[6,10],hwait:8,i_chunk:10,i_in_chunk:10,i_start:6,i_volum:10,idevicecount:8,ids:8,ifram:8,ignor:6,igroup:8,ikind:8,imag:[2,7],image_height:6,image_width:6,includ:4,index:[3,8],indic:8,inform:4,initi:[8,9],initial_paramet:9,initialize_camera:6,initopt:8,initoptionbyt:8,instal:3,institut:4,instruct:4,interact:4,interfac:[1,6,8],intern:[7,8],internal_frame_r:6,involv:8,iprop:8,iprop_arraybas:8,iprop_numberofel:8,ipropstep_el:8,ireserved1:8,ireserved3:8,is_complet:6,is_sav:6,is_saving_ev:10,is_send:10,is_set:6,is_waiting_ev:10,iscameraproperti:8,istr:8,its:4,iunit:8,just:4,keep:[6,8],kept:8,kind:8,know:8,known:8,kwarg:[6,9,10],kwd:8,lab:8,larva:2,laser:[5,6,7],laser_gui:[5,6],laser_set:7,lasercontrolwidget:7,laserset:6,last:8,later:[1,9],lateral_sync:9,latest:4,layout:7,lcm:6,least:8,left:8,length:[6,8],less:8,let:4,librari:8,light:[1,4],lightparam:[6,7],lightsheet:2,like:4,line:3,list:[3,6,8],littl:8,load:7,locat:8,lockbit:8,log:[5,6,9],log_ev:10,log_messag:10,log_queu:10,loggedev:[6,10],logger:[6,9],loggingprocess:[6,10],look:6,loop:[7,9],loop_condit:9,lot:8,lowercas:8,lowest:6,machin:4,main:[4,5,7],main_gui:[5,6],mainwindow:7,make:[6,8],mani:8,match:6,max:4,max_queue_s:[6,10],max_val:[4,6],maximum:4,mean:8,member:[4,8],memmov:8,memori:8,messag:10,method:[6,10],microscop:[3,4],might:1,min_val:[4,6],minimum:4,mock:[6,8],mockboard:9,mockcameraprocess:6,mockcoboltlas:8,mode:8,model:8,modifi:[4,7],modul:[3,4,5],modular:4,more:[4,8],multidimension:4,multipl:6,multiprocess:[6,9,10],munich:4,n_fill:6,n_fps_frame:6,n_imag:6,n_plane:[6,9,10],n_sampl:[6,9],n_samples_period:9,n_samples_tot:6,n_samples_waveform:10,n_skip_end:[6,9],n_skip_start:[6,9],n_volum:10,name:[6,8,10],napari:[4,7],navig:4,need:6,neurobiolog:4,new_refer:6,newfram:8,nframecount:8,niboard:9,nmaxchannel:8,nmaxview:8,nnewestframeindex:8,no_trigg:9,nois:6,noise_subtraction_act:6,noise_subtraction_on:10,noisesubtractionset:7,non:4,none:[6,7,8,9,10],nonetyp:9,notifi:6,notification_email:10,notifier_opt:6,now:[4,8],np_arrai:8,number:8,number_fram:8,numpi:[6,8],object:[6,7,8,9,10],obtain:6,obtain_noise_averag:6,omit_wid_camera:7,onc:8,one:8,onli:8,open:4,open_abstract_interfac:9,open_mockboard:9,open_napari:[5,6],open_niboard:9,optim:8,optimal_chunk_mb_ram:10,option:[6,8,10],other:4,otherwis:[4,8],out:8,output_dir:10,overridden:[6,10],overwrite_alert_popup:7,p_name:8,packag:5,param:7,param_qt:[6,7],paramet:[4,6,7],parameter_queu:[6,9],parametrizedqt:[6,7],part:3,particular:[4,8],path:[4,6,10],pathlib:10,paus:[6,9],pause_loop:6,pausedwidget:7,perform:8,perform_noise_subtract:7,piezo:[4,6,9],piezo_max:9,piezo_min:9,pip:3,planar:[6,9],planar_preview:6,planarscan:9,planarscanloop:9,planarscanningset:6,planarscanningwidget:7,planck:4,pop:4,popul:8,port:8,portugueslab:4,position_read:6,position_writ:4,posixpath:6,possibl:8,potenti:8,power:7,practic:4,prepar:4,preset:6,press:4,preview:[6,9],print_backlog:8,probabl:8,process:[5,6,9],process_fram:10,process_nam:10,progress:7,project:4,prompt:4,properli:8,properti:[7,8,9],property_nam:8,property_valu:8,provid:4,pyqt5:7,python:4,qcloseev:7,qdockwidget:7,qmainwindow:7,qrect:7,qregion:7,qtabwidget:7,qtcore:7,qtimer:7,qtwidget:7,queue:[9,10],queue_nam:10,qwidget:7,race:8,rang:8,read:[6,9],read_circular:6,read_config:6,read_task:9,readabl:8,readi:4,readout:4,receive_save_paramet:10,recommend:3,record:6,recordedwaveform:6,recycl:8,refer:8,refresh:7,refresh_imag:7,refresh_param_valu:7,refresh_progress_bar:7,refresh_widget:7,regular:8,releas:8,reli:4,remove_calibration_point:6,replac:[4,8],repo:6,repositori:4,requir:4,reserv:8,reset:10,reset_noise_subtract:6,restart_ev:[9,10],restart_scan:6,restore_fil:6,restore_tre:6,retrieve_paramet:10,roi:[7,8],roi_po:7,roi_siz:7,rolling_buff:5,rollingbuff:6,rowbyt:8,run:[4,6,8,10],run_camera:6,run_till_abort:8,same:8,sample_r:[6,9,10],sashimi:[1,2],sashimiev:6,save:[6,7],save_chunk:10,save_fil:6,save_gui:[5,6],save_loop:10,save_set:6,save_settings_gui:[5,6],save_tre:6,saver_queu:10,saveset:6,savewidget:7,saving_sign:10,saving_stop:6,savingparamet:10,savingsettingswidget:7,savingstatu:[6,10],sawtoothwaveform:6,scale:6,scan:[1,2,4,5,6,8],scanloop:[6,8],scanner:10,scanning_gui:[5,6],scanning_set:6,scanning_trigg:10,scanningerror:9,scanningset:6,scanningst:9,scanparamet:9,schema:3,scheme:8,scmo:8,scope_align:6,scope_instruct:6,scopealignmentinfo:6,scopeless:6,sdk4:8,section:6,seem:8,self:[7,8],send_camera_set:6,send_dispatcher_set:6,send_rec:10,send_scan_set:6,sens:8,sequenc:8,set:[4,6,7,8],set_curr:8,set_full_size_fram:7,set_impuls:6,set_locationbutton:7,set_noise_subtraction_mod:7,set_roi:7,set_save_loc:7,setacqmod:8,setpropertyvalu:8,setsubarraymod:8,setup:8,setup_task:9,share:8,shared_arrai:[9,10],sheet:4,should:8,show:4,show_dialog_box:7,shuffl:8,shutdown:8,sig_params_load:7,simpl:6,sinc:8,single_plane_set:6,singleplanescanningwidget:7,singleplaneset:6,size:[7,8],slow:8,softwar:[3,8],some:8,sort:8,sortedpropertytextopt:8,sourc:[1,4],space:8,specifi:8,stacksav:10,stage:1,start:[3,6,8,9],start_experi:6,start_experiment_from_scann:10,startacquisit:8,starttrigg:6,state:[5,7,9],statuswidget:7,stop:8,stop_ev:[6,9,10],stopacquisit:8,storag:8,storm:8,str:[6,10],stream:7,streaming_sav:[5,6],string:6,structur:8,stytra_address:10,stytra_comm:[5,6],stytracomm:10,sub:[6,8,10],subarrai:6,subject:8,submodul:5,subpackag:5,subtract:6,support:[4,8],supportev:8,sync:6,sync_coef:9,system:4,target_param:10,tcp:10,technic:4,templat:6,termin:4,test:8,text:8,textbyt:8,thi:[4,6,8],thing:6,three:1,through:4,time:8,timeout:[6,7,8],timer:7,timestamp:8,titl:7,to_writ:6,toggl:7,toggle_roi_displai:7,toml:6,too:8,top:8,track:8,travi:[6,10],tri:8,trianglewaveform:6,trigger:[6,9],trigger_and_receive_dur:10,trigger_condit:10,trigger_exp_from_scann:9,trigger_mod:6,trigger_stytra:6,triggeringparamet:9,triggermod:6,tupl:[6,9,10],turn:8,two:[2,8],type:[6,8],uint16:6,underscor:8,union:[8,9],univers:4,unknown:8,unlockbit:8,until:8,updat:[7,8],update_align:7,update_camera_info:7,update_contrast_limit:7,update_curr:7,update_framer:6,update_label:7,update_puls:7,update_roi:7,update_roi_info:7,update_saved_status_queu:10,update_set:9,update_statu:7,updatebtntext:7,usag:[4,6],use:8,used:[2,8],user:[4,8],uses:8,using:8,util:5,val:6,valu:[6,8],valuedefault:8,valuemax:8,valuemin:8,valuestep:8,vendor:4,version:8,via:7,viewer:[4,7],viewingwidget:7,vmax:[6,9],vmin:[6,9],volt:4,voltag:4,volum:[7,10],volume_preview:6,volumedispatch:10,volumer:10,volumescanningwidget:7,volumetr:9,volumetricscanloop:9,voxel_s:[7,10],wai:6,wait:8,wait_ev:6,wait_sign:[9,10],waiting_ev:10,waiting_for_trigg:6,want:[4,8],warn:8,waveform:[4,5],waveform_gui:[5,6],waveform_queu:9,waveformwidget:7,welcom:4,when:8,which:8,whole:4,widget:7,width:8,without:4,would:8,wrap_up:6,write:[4,6,9],write_circular:6,write_config_valu:6,write_default_config:6,write_entri:10,write_task_xi:9,write_task_z:9,writeabl:8,written:6,xy_board:6,xy_front:9,xy_later:9,xyscan:9,yml:4,you:[4,8],your:4,z_board:[4,6],z_frontal:9,z_later:9,z_piezo:9,z_set:6,zebrafish:2,zenodo:8,zero:8,zhuang:8,zmanual:9,zrecordingset:6,zscan:9,zset:6,zsync:9},titles:["Configuring Sashimi","Code organization","Microscope hardware","Welcome to the Sashimi documentation!","Sashimi","sashimi","sashimi package","sashimi.gui package","sashimi.hardware package","sashimi.hardware.scanning package","sashimi.processes package"],titleterms:{"new":4,altern:2,calibration_gui:7,camera:6,camera_gui:7,code:1,command:4,config:6,configur:[0,4],content:[6,7,8,9,10],creat:4,dispatch:10,document:3,environ:4,event:6,from:4,gui:7,hamamatsu_camera:8,hardwar:[2,8,9],here:4,instal:4,interfac:9,laser:8,laser_gui:7,line:4,list:2,log:10,main:6,main_gui:7,microscop:2,mock:9,modul:[6,7,8,9,10],open_napari:7,organ:1,packag:[6,7,8,9,10],part:2,pip:4,process:10,recommend:4,rolling_buff:6,sashimi:[0,3,4,5,6,7,8,9,10],save_gui:7,save_settings_gui:7,scan:[9,10],scanloop:9,scanning_gui:7,schema:2,softwar:4,start:4,state:6,streaming_sav:10,stytra_comm:10,submodul:[6,7,8,9,10],subpackag:[6,8],titl:4,util:6,waveform:6,waveform_gui:7,welcom:3}})