function batch_repeat444_centerline()
%BATCH_REPEAT444_CENTERLINE Repeat centerline unit cells to 4x4x4 and export JSON.
clear; clc;

scriptDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(fileparts(scriptDir));
addpath(genpath(fullfile(rootDir, 'matlab')));
srcMatDir = fullfile(rootDir, 'data', 'base', 'mat');
repMatDir = fullfile(rootDir, 'data', 'rep444', 'mat');
jsonDir = fullfile(rootDir, 'data', 'rep444', 'json');

if ~exist(repMatDir, 'dir'); mkdir(repMatDir); end
if ~exist(jsonDir, 'dir'); mkdir(jsonDir); end

repeatN = [4 4 4];
cellSizeMM = 20.0;
branchName = '4x4x4';
files = dir(fullfile(srcMatDir, '*.mat'));
if isempty(files)
    error('No centerline .mat files found. Run batch_generate_curved_x_centerline first.');
end

for i = 1:numel(files)
    S = load(fullfile(files(i).folder, files(i).name));
    repeatedPaths = repeat_centerline_lattice(S.strutPaths, repeatN);

    [~, baseName, ~] = fileparts(files(i).name);
    caseName = [baseName '_rep444'];

    R = S;
    R.caseName = caseName;
    R.branchName = branchName;
    R.repeatN = repeatN;
    R.cellSizeMM = cellSizeMM;
    R.radiusMM = S.radiusNorm * cellSizeMM;
    R.H0_mm = repeatN(3) * cellSizeMM;
    R.A0_mm2 = (repeatN(1) * cellSizeMM) * (repeatN(2) * cellSizeMM);
    R.strutPaths = repeatedPaths;

    repMatFile = fullfile(repMatDir, [caseName '.mat']);
    save(repMatFile, '-struct', 'R');

    jsonFile = fullfile(jsonDir, [caseName '.json']);
    export_centerline_to_json(R, jsonFile);
    fprintf('Exported: %s\n', jsonFile);
end
end
