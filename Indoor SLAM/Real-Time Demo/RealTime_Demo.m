function [data,sd] = RealTime_Demo(NetworkIp,socket)
    %% Real-time Demo
    % Description: Real-Time demo to show how the framework works.
    % Cell phone sensor data is streamed over a network and tcp port and is
    % then processed to display the step-detection/Heading algorithm.  This
    % data is then used to generate and segment trajectories in order to
    % classify features of the indoor environment and map out the floor
    % space.
    %
    % input: Network, socket
    % output: real-time visualization of step detection/heading
    %%        % string      % int
    t = tcpip(NetworkIp , socket);
    t.InputBufferSize = 512*3;
    fopen(t);
    % Initialize data structure
    data.H     = [];
    data.loc   = [];
    data.acc   = [];
    data.gyr   = [];
    data.mot   = [];
    data.time  = [];
    data.trate = [];
    data.datenum  = [];
    new_times     = [];
    sd            = [];
    
    % initialize plot settings
    figure;
    set(gcf,'position',[80 80 1000 600]);
    axid = subplot(2,1,1);
    hold(axid,'on');
    axid_dir = subplot(2,1,2);
    set(axid,'position',[.1 .2 .5 .6]);
    set(axid_dir,'position',[.65 .25 .35 .4]);
    polar(axid_dir,0,0);
    
    %% Visualize data in real-time
    % Initialize Real-time conditions
    timeout = 0;
    buffer  = 100;
    prev_dp = 0;
    prevstep= 0;
    tic;
    
    % End visualization if data isn't received within 3s
    while timeout < 3  
        % Parse tcp handle for available data
        if t.BytesAvailable > 0
            A = fscanf(t);
            foutput = strsplit(A,';');
            state   = str2double(foutput{end});
            if ~isnan(state)
                tic;
                % Log pertinent data into data struct
                data.loc  = vertcat(data.loc,str2double(foutput(6:7)));
                data.acc  = vertcat(data.acc,str2double(foutput(21:23)));
                data.gyr  = vertcat(data.gyr,str2double(foutput(25:27)));
                data.mot  = vertcat(data.gyr,str2double(foutput(29:31)));
                data.H    = vertcat(data.H,str2double(foutput(17)));
                data.datenum = vertcat(data.datenum,datenum(foutput{1},'yyyy-mm-dd HH:MM:SS.FFF'));
                % Update plot every 100 samples (1s)
                if buffer < size(data.loc,1)-prev_dp
                    % Plot raw/smoothed cell-phone accelerometer data
                    if size(data.loc,1) > 500
                        % after 5 seconds, check for a step 
                        [sd,~,~] = StepDetection_Demo(data);
                        curstep  = length(sd.len);
                        if prevstep < curstep
                            fprintf('Step detected\tCount: %d\tDistance traveled: %d(m)\tDirection %d(deg)\n',curstep,sum(sd.len),sd.direction(end));
                            prevstep = curstep;
                        end
                        leg = VisualizeData(axid,data.datenum,sd,true,axid_dir); 
                        set(axid,'ylim',[0.4 2]);
                    else
                        leg = VisualizeData(axid,data.datenum,data,false,[]);
                    end
                    prev_dp = size(data.loc,1);
                    % Set title/labels of plot
                    title(axid,sprintf('Real-time Visualization\nAcceleration vs. time'));
                    xlabel(axid,'Times (s)');
                    ylabel(axid,'Acceleration');
                    set(axid,'fontsize',20);
                    legend(axid,leg);
                end
            end
        end
        timeout = toc;
    end
    % Safe shut-down
    fprintf('Timeout Condition reached...\n\tShutting down Demo\n');
    close all;
    data.time = new_times;
    fclose(t);
    delete(t);
    clear t
end

function leg = VisualizeData(axid,datenums,data,st_state,axid_dir)
    % Display Step and Heading of user carrying cell-phone
    if st_state
        plot(axid,data.time(1:end-1),data.sacc(1:end-1),'b','linewidth',1.5);
        leg = {'Smoothed Data'};
        % Plot Step Detection peaks with red/blue circles 
        if ~isempty(data.smax)
            plot(axid,data.smax(1:end-1,1),data.smax(1:end-1,2),'ro','linewidth',1);
            x = [0 data.direction(end,1)/(2*pi)];
            y = [0 data.len(end)];
            polar(axid_dir,x,y);
            leg = {'Smoothed Data','Step'};
        end
        set(axid,'xlim',[data.time(end)-10 data.time(end)]);    
    else
        % plot x,y,z axis accelerometer data
        new_times = ReformatTime(datenums);
        plot(axid,new_times(1:end-1),data.acc(1:end-1,1),'b');
        plot(axid,new_times(1:end-1),data.acc(1:end-1,2),'r');
        plot(axid,new_times(1:end-1),data.acc(1:end-1,3),'g');
        leg = {'X-axis','Y-axis','Z-axis'};
        if new_times(end) > 5
            set(axid,'xlim',[new_times(end)-10 new_times(end)]);    
        end
    end
    drawnow;
end

function new_times = ReformatTime(datenums)
    % reformat time vector
    datevecs     = datevec(datenums);
    new_times    = datevecs(:,5)*60 + datevecs(:,6); % supports minutes
    new_times    = vertcat(0,cumsum(diff(new_times)));
end

function [stepData,Lstep,Rstep] = StepDetection_Demo(data)
    %% Step detection
    % Calculates the length and heading of each step taken in 
    % order to generate user trajectories based on cell phone accelerometer
    % data.  Uses two different methods: Step agnostic & Left/Right Step
    % detection.
    %
    % input: raw data
    % Output: stepData, direction, length, number of left & right steps
    
    % HARDCODED VARIABLES
    smoothfreq = 5; % Smooth to 5hz (0.2)
    cutofftime = 5; % Exclude data within first 5 sec and last 5 secs
    highband_time   = .30; %highpass filter set at .35s
    alpha      = 0.9;  % step agnostic (step length coefficient)
    sthreshold = 1.2;  % based on observation from data
    Lalpha     = 1.33; % left-foot (step length coefficient)
    Ralpha     = .6;   % right-foot (step length coefficient)
    
    % Initilize output variables
    stepData.sdetTS    = [];
    stepData.smax      = [];
    stepData.smin      = [];
    stepData.sthresh   = [];
    stepData.direction = [];
    stepData.len       = [];
    Lstep              = [];
    Rstep              = [];
    
    % reformat time (universal sampling time)
    timevals   = datevec(data.datenum);
    time       = timevals(:,5)*60 + timevals(:,6);
    time       = vertcat(0,cumsum(diff(time)));
    
    % - Collected at 100hz, use 10 sample windows for processing (10hz)
    sampfreq   = mean(diff(time)); %avg samp freq
    tot_acc    = sqrt(data.acc(:,1).^2+data.acc(:,2).^2+data.acc(:,3).^2);
    swindow    = (sampfreq^-1)/smoothfreq; %window size --> 10hz
    
    %  record moving average
    stot_acc        = smooth(tot_acc,swindow);
    stepData.sacc   = stot_acc;
    stepData.time   = time;

    %find first steps
    steps         = logical(vertcat(0,diff(stot_acc > sthreshold) > 0)); 
    sampindex     = 1:length(steps);
    steps         = sampindex(steps);
    stimes        = time(steps);
    
    % restrict step detections using band pass filter & datacutoff point
    highband      = highband_time/sampfreq; 
    datacutoff    = [cutofftime time(end)-cutofftime];
    Constraint1   = stimes > datacutoff(1) & stimes < datacutoff(2);
    Constraint2   = logical(horzcat(0,(highband<diff(steps))))';
    stimes = stimes(Constraint1 & Constraint2);

    % Compute peaks and valleys
    sind2 = find(ismember(time, stimes));
    
    % If there is a step
    if ~isempty(sind2)
        sind2 = sind2(logical(vertcat(1,diff(sind2) > 1)));
        sind1 = vertcat(sind2-round(highband));
        sind3 = vertcat(sind2+round(highband));
                           % LO   SD     HI
        sindices = horzcat(sind1,sind2,sind3);
        % Initialize peaks/valleys,heading
        apeak     = zeros(length(stimes),2);
        avalley   = zeros(length(stimes),2);
        direction = zeros(length(stimes),4); % mean,min,detect,max
        len       = zeros(length(stimes),1);
        for i_step = 1:size(sindices,1)
            lwindow = sindices(i_step,2)-sindices(i_step,1);
            [avalley(i_step,2),avalley(i_step,1)] = min(stot_acc(sindices(i_step,1):sindices(i_step,2)));
            avalley(i_step,1) = time(sindices(i_step,2)-(lwindow-avalley(i_step,1)));
            [apeak(i_step,2),apeak(i_step,1)]   = max(stot_acc(sindices(i_step,2):sindices(i_step,3)));
            apeak(i_step,1)   = time(sindices(i_step,2)+apeak(i_step,1));
            temp_peak = apeak(i_step,2)-avalley(i_step,2);
            % direction
                % take average from start to finish of step
            heading_indices   = sindices(i_step,logical([1 0 1])); 
            temp_direction    = data.H(heading_indices(1):heading_indices(2));
            
                % flip heading degrees to fit into 
            temp_direction(temp_direction > 180) = temp_direction(temp_direction > 180) - 360;
            direction(i_step,:) = [mean(temp_direction) data.H(sindices(i_step,1)) data.H(sindices(i_step,2)) data.H(sindices(i_step,3))];
            
                % length (determined by hardcoded [alpha])
            len(i_step,:)     = temp_peak*alpha;
        end
        
        % Record Step Detection DAta
        stepData.sdetTS = stimes;
        stepData.smax   = apeak;
        stepData.smin   = avalley;
        stepData.sthresh= sthreshold;
        stepData.direction = direction;
        stepData.len       = len;
        
        % Differentiate between left/right foot
        temp_peak = apeak(:,2)-avalley(:,2);
        Lstep = [stimes(temp_peak < alpha) temp_peak(temp_peak < alpha).*Lalpha];
        Rstep = [stimes(temp_peak >= alpha) temp_peak(temp_peak >= alpha).*Ralpha];    
    end
end
