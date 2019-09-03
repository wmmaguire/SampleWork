%Segmentation
function [segment_ref,segment_class,segment]= segment_trajectory(traj_list,traj_x,nb_segment_total)
    
    threshold = 45;
    i = 1;
    count = 1;
    index_segment = nb_segment_total;
    segment_class = zeros(size(traj_list,1),1);
    segment_ref = zeros(size(traj_list,1),1);
    while(i<=size(traj_list,1)) 
        %Initial heading of the segment
        heading = traj_list(i,3);
        segment_class(i)=count;
        segment_ref(i)=index_segment;
        %segment{count}.points[]
        j=1;
     
        while(i+j<=size(traj_list,1) && abs(heading-traj_list(i+j,3))<threshold)
            %Attribute the value to the cluster
            segment_class(i+j)=count;
            segment_ref(i+j)=index_segment;
            j=j+1;
        end
        count= count+1;
        index_segment = index_segment+1;
        i=i+j;
    end
    
    
    %segment= zeros(length(unique(segment_class)),4);
    %First column average time
    %Second column segment length
    %Third/Fourth column Center of segment X Y
    av_time = average_time(traj_list, segment_class);
    seg_length= segment_length(traj_list, segment_class);
    center= center_segment(traj_list, segment_class,traj_x);
    
    segment =[av_time, seg_length ,center];
    
end


function av_time = average_time(traj_list, segment_class)
    nb_segment = length(unique(segment_class));
    av_time = zeros(nb_segment,1);    
    init_time= traj_list(1,1);
    count = 0;
    j =1;
    for i=1:size(traj_list,1)
        %End of the list
        if (i==size(traj_list,1))
            av_time(nb_segment)=(traj_list(i,1)-init_time)/count;
        elseif (segment_class(i,1)==segment_class(i+1,1))
           %Increment number of steps
            count =count+1; 
        else
            %End of segment
            av_time(j)= (traj_list(i+1,1)-init_time)/(count+1);
            j=j+1;
            count=0;
            init_time=traj_list(i+1,1);
        end
    end
end

function seg_length=segment_length (traj_list, segment_class)
    nb_segment = length(unique(segment_class));
    seg_length = zeros(nb_segment,1);
    for i=1:size(traj_list,1)
        seg_length(segment_class(i))=seg_length(segment_class(i))+traj_list(i);
    end
end

function center= center_segment(traj_list, segment_class, traj_x)
    nb_segment = length(unique(segment_class));
    center = zeros(nb_segment,2);
    init_position = traj_x(1,:);
    j=1;
   
    for i=1:size(traj_list,1)
        if (i==size(traj_list,1))
            center(nb_segment,:)=(traj_x(i+1,:)-init_position)/2+init_position;
        elseif (segment_class(i,1)==segment_class(i+1,1))
           %Increment number of steps 
        else
            %End of segment
            center(j,:)= (traj_x(i+1,:)-init_position)/2+init_position;
            j=j+1;
            init_position=traj_x(i+1,:);
        end
    end
    
end
