function batch_repeat222_centerline()
%BATCH_REPEAT222_CENTERLINE Repeat centerline unit cells to 2x2x2 and export JSON.
clear; clc;

scriptDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(fileparts(scriptDir));
addpath(genpath(fullfile(rootDir, 'matlab')));
srcMatDir = fullfile(rootDir, 'data', 'base', 'mat');
repMatDir = fullfile(rootDir, 'data', 'rep222', 'mat');
jsonDir = fullfile(rootDir, 'data', 'rep222', 'json');

if ~exist(repMatDir, 'dir'); mkdir(repMatDir); end
if ~exist(jsonDir, 'dir'); mkdir(jsonDir); end

repeatN = [2 2 2];
cellSizeMM = 20.0;
branchName = '2x2x2';
files = dir(fullfile(srcMatDir, '*.mat'));
if isempty(files)
    error('No centerline .mat files found. Run batch_generate_curved_x_centerline first.');
end

for i = 1:numel(files)
    S = load(fullfile(files(i).folder, files(i).name));
    repeatedPaths = repeat_centerline_lattice(S.strutPaths, repeatN);

    [~, baseName, ~] = fileparts(files(i).name);
    caseName = [baseName '_rep222'];

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
