const value = this.toolResultProxy
                ? await this.toolResultProxy.proxy({ value: providerValue })
                : providerValue;
            const bounded = boundedResult(value, context.maxResultChars);
            const resultError = failedResultError(value);
            activeAudit.success = resultError === undefined;
            if (resultError)
                activeAudit.error = resultError;
            activeAudit.resultChars = bounded.chars;
            activeAudit.resultTruncated = bounded.truncated;
