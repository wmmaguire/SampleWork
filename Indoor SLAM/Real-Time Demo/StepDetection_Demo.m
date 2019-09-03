function [stepData,direction,len,Lstep,Rstep] = StepDetection_Demo(data)
    %% Step detection
    % Reference: Ms. Najme Zehra Naqvi et al.
    % Output: stepData
    % HARDCODED VARIABLES
    smoothfreq = 5; % Smooth to 5hz (0.2)
    cutofftime = 5; % Exclude data within first 5 sec and last 5 secs
    highband_time   = .30; %highpass filter set at .35s
    alpha      = 0.9;
    Lalpha     = 1.33;
    Ralpha     = .6;
    % reformat time (universal sampling time)
    timevals   = datevec(data.time);
    time       = timevals(:,5)*60 + timevals(:,6); % supports minutes
    time       = vertcat(0,cumsum(diff(time)));
    % - Collected at 100hz, use 10 sample windows for processing (10hz)
    sampfreq   = mean(diff(time)); %avg samp freq
    tot_acc    = sqrt(data.acc(:,1).^2+data.acc(:,2).^2+data.acc(:,3).^2);
    swindow    = (sampfreq^-1)/smoothfreq; %window size --> 10hz
    %    % moving average
    stot_acc   = smooth(tot_acc,swindow);
    %% Calibrate Standing Detection  (stand still) --> 10hz
    movingstd  = zeros(length(1:ceil(swindow):500),1);
    movingmean = zeros(length(1:ceil(swindow):500),1);
    ind = 1;
    for i = 1:ceil(swindow):500
        movingstd(ind)  = std(stot_acc(i:i+floor(swindow)));
        movingmean(ind) = mean(stot_acc(i:i+floor(swindow)));
        ind = ind +1;
    end
    % Detect Starting point (stand still) --> 10hz
    sthreshold = mean(movingmean) + mean(movingmean)*0.2; % based on observation from data
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
    stepData.sacc   = stot_acc;
    stepData.time   = time;
    stepData.sdetTS = stimes;
    stepData.smax   = apeak;
    stepData.smin   = avalley;
    stepData.sthresh= sthreshold;
    % Differentiate between left/right foot
    temp_peak = apeak(:,2)-avalley(:,2);
    Lstep = [stimes(temp_peak < alpha) temp_peak(temp_peak < alpha).*Lalpha];
    Rstep = [stimes(temp_peak >= alpha) temp_peak(temp_peak >= alpha).*Ralpha];
        % Record Coordinate Estimate
%     %% Plot data (Diagnostics)
%     figure; hold on; 
%     plot(time,stot_acc,'k','linewidth',2);
%     plot(apeak(:,1),apeak(:,2),'ro');
%     plot(avalley(:,1),avalley(:,2),'bo');
%     set(gca,'ylim',[.6 1.9]);
%     title(sprintf('Step Detection for Total Acc\nMoving Avg'));
%     legend({'Filtered Acc Data','Max Acc during step','Min Acc during step'});
%     ylabel('Total Acceleration');
%     xlabel('Time (s)');
%     set(gca,'fontsize',20);
%%% Plot Heading
%     figure; 
%     % Heading
%     temp_heading = data.H;
%     temp_heading(temp_heading > 180) = temp_heading(temp_heading > 180) - 360;
%     plot(time,temp_heading,'b','linewidth',2);
%     hold on;
%     ylabel('Degrees');
%     xlabel('Time');
%     title('True Heading (degrees)');
%     set(gca,'fontsize',20);
%     set(gca,'ylim',[-180 180]);
%     % Look at H_ST to determine direction
%             % using TS of step detected
%     plot(stepData.sdetTS(temp_peak >= alpha),direction(temp_peak >= alpha,1),'ro','linewidth',1);
%     plot(stepData.sdetTS(temp_peak < alpha),direction(temp_peak < alpha,1),'go','linewidth',1);
%     
%     legend({'Heading','Right step','Left step'});
end

