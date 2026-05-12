function batch_generate_curved_x_centerline()
%BATCH_GENERATE_CURVED_X_CENTERLINE Generate random curved-X centerline samples.
clear; clc;

scriptDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(fileparts(scriptDir));
addpath(genpath(fullfile(rootDir, 'matlab')));
outRoot = fullfile(rootDir, 'data', 'base');
matOutDir = fullfile(outRoot, 'mat');
figOutDir = fullfile(outRoot, 'preview');

if ~exist(matOutDir, 'dir'); mkdir(matOutDir); end
if ~exist(figOutDir, 'dir'); mkdir(figOutDir); end

% Geometry settings
nPtsPerArm = 61;
refAxis = [0 0 1];

% Random sampling settings
% radiusNorm is normalized by one unit-cell size.
targetN = 16;
rngSeed = 1;
rng(rngSeed);
radiusMin = 0.030;
radiusMax = 0.045;
bendMin   = 0.060;
bendMax   = 0.120;

savePreviewPNG = true;
previewEvery = 4;

caseNames = strings(targetN,1);
radiusVals = zeros(targetN,1);
bendVals = zeros(targetN,1);
matFiles = strings(targetN,1);
previewFiles = strings(targetN,1);

for i = 1:targetN
    radiusNorm = radiusMin + (radiusMax-radiusMin) * rand();
    bendAmp = bendMin + (bendMax-bendMin) * rand();

    caseName = sprintf('cs_rand_%05d_b%03d_r%03d', ...
        i, round(1000*bendAmp), round(1000*radiusNorm));

    sample = generate_curved_x_centerline(nPtsPerArm, bendAmp, refAxis, radiusNorm);
    sample.caseName = caseName;
    sample.rngSeed = rngSeed;

    matFile = fullfile(matOutDir, [caseName '.mat']);
    save_centerline_sample_mat(matFile, sample);

    pngFile = "";
    if savePreviewPNG && mod(i, previewEvery) == 0
        pngFile = fullfile(figOutDir, [caseName '.png']);
        preview_centerline_lattice(sample.strutPaths, pngFile, caseName);
    end

    caseNames(i) = caseName;
    radiusVals(i) = radiusNorm;
    bendVals(i) = bendAmp;
    matFiles(i) = string(matFile);
    previewFiles(i) = string(pngFile);
end

T = table((1:targetN).', caseNames, radiusVals, bendVals, matFiles, previewFiles, ...
    'VariableNames', {'CaseID','CaseName','RadiusNorm','BendAmp','MatFile','PreviewFile'});
summaryFile = fullfile(outRoot, 'summary_centerline.csv');
writetable(T, summaryFile);

fprintf('Generated %d centerline samples.\n', targetN);
fprintf('Summary: %s\n', summaryFile);
end
