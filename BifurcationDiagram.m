clear function_generator
function_generator = visadev("USB0::0x0400::0x09C4::DG1F134500132::0::INSTR");

write(function_generator,"FREQ 1e5")
write(function_generator,"VOLT 1")

PS2000aConfig

ps2000aDeviceObj = icdevice('picotech_ps2000a_generic.mdd', '');
set(ps2000aDeviceObj, 'displayOutput', PicoConstants.FALSE);


connect(ps2000aDeviceObj)
%Channel, Enabled, Type, Range, Offset
invoke(ps2000aDeviceObj, 'ps2000aSetChannel', 0, 0, 1, 5, 0);
invoke(ps2000aDeviceObj, 'ps2000aSetChannel', 1, 1, 1, 5, 0);
% status.resolution = invoke(ps2000aDeviceObj, 'ps2000aSetDeviceResolution', 15);  
% set(ps2000aDeviceObj, 'resolution', 15);


timebaseIndex = 13;

set(ps2000aDeviceObj, 'timebase', timebaseIndex);

blockGroupObj = get(ps2000aDeviceObj, 'Block');
blockGroupObj = blockGroupObj(1);

startIndex              = 0;
segmentIndex            = 0;
downsamplingRatio       = 1;
downsamplingRatioMode   = ps2000aEnuminfo.enPS2000ARatioMode.PS2000A_RATIO_MODE_NONE;

%Start Loop Here
N = 1000;
chB = zeros([8192,N]);

for i=1:N

    voltage_string = num2str((i/N)*19+1);

    write(function_generator,"VOLT " + voltage_string)

    pause(0.5)

    [status.runBlock] = invoke(blockGroupObj, 'runBlock', 0);


    [numSamples, overflow, chA, chB(:,i)] = invoke(blockGroupObj, 'getBlockData', startIndex, segmentIndex, ...
                                                downsamplingRatio, downsamplingRatioMode);
    [status.stop] = invoke(ps2000aDeviceObj, 'ps2000aStop');

    disp(num2str(i))
end


disconnect(ps2000aDeviceObj);
delete(ps2000aDeviceObj);
%% 

figure(5)
plot(chB(:,199))

%%
T = (13-2)/125000000;
Fs = 1/T;
newchA = chB;
X = zeros(size(newchA));

for i=1:size(newchA,2)
    X(:,i) = lowpass(newchA(:,i),100000,Fs);
end
filtered_chB = X;
% %%
% figure(1)
% plot(newchA(:,1000))
% hold on
% plot(X(:,1000))
% hold off
% legend('A','X')

% %%
% figure(5)
% plot(chB(:,800))
%%
% newchA = chB;
% avg_size = 5;
% mask = ones(1,avg_size)/avg_size;
% filtered_chB = filter(mask,1,filtered_chB);

%%
figure(6)
plot(filtered_chB(:,399))
% hold on
% plot(newchA(:,199))
hold off
legend('filtered','raw')
xlabel('samples')
ylabel('Voltage over Resistor (mV)')


%%

N = size(filtered_chB,2);
total = {};
for i=1:N
    [pks,loc] = findpeaks(filtered_chB(:,i),'MinPeakDistance',50);
    total{i} = pks;
end

minimum = int32(min(cellfun('size',total,1)));

for i=1:N
    total{i} = total{i}(15:minimum-5);
end

L = N-10;
new = cell2mat(total);
figure(10)
scatter(total{L}(1:end-1),total{L}(2:end))
xlabel('x_n')
ylabel('x_{n+1}')
%%

X = zeros([minimum-20,N]);
Y=X;
Z = X;
for i=1:N
    X(:,i) = new(1:end-1,i);
    Y(:,i) = new(2:end,i);
    Z(:,i) = i/N*19*ones([minimum-20,1]) + 1;
end

X = reshape(X,[],1);
Y = reshape(Y,[],1);
Z = reshape(Z,[],1);


figure(14)
scatter3(X,Y,Z,0.5)

figure(15)
scatter(Z,X,2,'filled')
xlabel("Driving Amplitude (Volts)")
ylabel("Local Peak Heigh (mV)")

%%
% sel_i = 500;
% selection = filtered_chB(:,sel_i);
% new_mask = islocalmax(selection) | islocalmin(selection);
% 
% extrema = selection(new_mask);
%% 

% 
% pxx = pwelch(filtered_chB);
% 
% figure(1)
% plot(pxx(1:30,800))


%%
% thing = histcounts2(Z,X,2000);
% 
% mask_conv = ones(3);
% %thing = conv2(thing,mask_conv,'same');
% 
% figure(20)
% imshow(flipud(thing.'),[0,3])
%%
writematrix(X,'bifur_100khz_X.csv')
writematrix(Z,'bifur_100khz_Z.csv')