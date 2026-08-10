const details = {
    success: input.success,
    trace: cloneTrace(input.trace),
    ...(input.outputFormat ? { outputFormat: input.outputFormat } : {}),
};
