%%Trajectory generation

%Input Time, Length step, heading value

%Output, Time, X,Y of different nodes

function [timed,X,Y] = generate_trajectory(traj_list, initial_position,scale)
    
X= zeros(size(traj_list,1),1);
Y= zeros(size(traj_list,1),1);
    X(1) =initial_position(1);
    Y(1) =initial_position(2);
    for i=1:size(traj_list,1)
        X(i+1)= X(i)-scale*traj_list(i,2)*sind(traj_list(i,3));
        Y(i+1)= Y(i)+scale*traj_list(i,2)*cosd(traj_list(i,3));
    end
 timed = traj_list(:,1);

end