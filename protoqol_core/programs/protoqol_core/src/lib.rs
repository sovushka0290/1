use anchor_lang::prelude::*;
use anchor_lang::solana_program::system_instruction;

declare_id!("EdrjHLN9K9eogJ5Pui8WYJRAghdN4knAdAoDcZesAirc");

// Foundation Master authority for protocol config
const PROTOCOL_ADMIN: &str = "98EJYhcrJHWYsdRvTg5Tg2zi47midrFHBhdsrdnoLezh";

#[program]
pub mod protoqol_core {
    use super::*;

    pub fn initialize_protocol(ctx: Context<InitializeProtocol>) -> Result<()> {
        let stats = &mut ctx.accounts.stats;
        stats.total_deeds = 0;
        stats.admin = ctx.accounts.admin.key();
        Ok(())
    }

    pub fn add_oracle(ctx: Context<ManageOracle>, oracle_pubkey: Pubkey) -> Result<()> {
        let registry = &mut ctx.accounts.oracle_registry;
        registry.oracle = oracle_pubkey;
        registry.is_active = true;
        msg!("New Biy Oracle authorized: {}", oracle_pubkey);
        Ok(())
    }

    pub fn propose_deed(
        ctx: Context<ProposeDeed>,
        deed_id: String,
        mission_id: String,
        reward_amount: u64
    ) -> Result<()> {
        let deed = &mut ctx.accounts.deed;
        deed.nomad = ctx.accounts.nomad.key();
        deed.proposer = ctx.accounts.proposer.key();
        deed.mission_id = mission_id;
        deed.reward_amount = reward_amount;
        deed.votes_adal = 0;
        deed.votes_aram = 0;
        deed.resolved = false;
        deed.timestamp = Clock::get()?.unix_timestamp;

        // Transfer funds from proposer to deed escrow (PDA)
        let ix = system_instruction::transfer(
            &ctx.accounts.proposer.key(),
            &ctx.accounts.deed.key(),
            reward_amount,
        );
        anchor_lang::solana_program::program::invoke(
            &ix,
            &[
                ctx.accounts.proposer.to_account_info(),
                ctx.accounts.deed.to_account_info(),
                ctx.accounts.system_program.to_account_info(),
            ],
        )?;

        msg!("ProtoQol Deed Proposed: {} for reward {}", deed_id, reward_amount);
        Ok(())
    }

    pub fn vote_deed(
        ctx: Context<VoteDeed>,
        _deed_id: String,
        verdict_adal: bool
    ) -> Result<()> {
        let deed = &mut ctx.accounts.deed;
        require!(!deed.resolved, ErrorCode::DeedAlreadyResolved);

        if verdict_adal {
            deed.votes_adal += 1;
        } else {
            deed.votes_aram += 1;
        }

        msg!("Biy Oracle {} voted. ADAL: {}, ARAM: {}", 
            ctx.accounts.oracle.key(), deed.votes_adal, deed.votes_aram);

        // Auto-resolution if 3 votes reached (Consensus)
        if deed.votes_adal + deed.votes_aram >= 3 {
            deed.resolved = true;
            if deed.votes_adal > deed.votes_aram {
                // ADAL: Transfer reward to nomad
                **deed.to_account_info().try_borrow_mut_lamports()? -= deed.reward_amount;
                **ctx.accounts.nomad.try_borrow_mut_lamports()? += deed.reward_amount;
                msg!("Consensus: ADAL. Reward released to nomad.");
            } else {
                // ARAM: Return reward to B2B proposer
                **deed.to_account_info().try_borrow_mut_lamports()? -= deed.reward_amount;
                **ctx.accounts.proposer.try_borrow_mut_lamports()? += deed.reward_amount;
                msg!("Consensus: ARAM. Reward returned to proposer.");
            }
        }

        Ok(())
    }
}

#[derive(Accounts)]
#[instruction(oracle_pubkey: Pubkey)]
pub struct ManageOracle<'info> {
    #[account(
        init,
        payer = admin,
        space = 8 + OracleRegistry::INIT_SPACE,
        seeds = [b"oracle", oracle_pubkey.as_ref()],
        bump
    )]
    pub oracle_registry: Account<'info, OracleRegistry>,
    #[account(mut, constraint = admin.key().to_string() == PROTOCOL_ADMIN)]
    pub admin: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct InitializeProtocol<'info> {
    #[account(init, payer = admin, space = 8 + ProtocolStats::INIT_SPACE, seeds = [b"stats"], bump)]
    pub stats: Account<'info, ProtocolStats>,
    #[account(mut, constraint = admin.key().to_string() == PROTOCOL_ADMIN)]
    pub admin: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
#[instruction(deed_id: String)]
pub struct ProposeDeed<'info> {
    #[account(
        init,
        payer = proposer,
        space = 8 + DeedRecord::INIT_SPACE,
        seeds = [b"deed", deed_id.as_bytes()],
        bump
    )]
    pub deed: Account<'info, DeedRecord>,
    /// CHECK: Target recipient
    pub nomad: AccountInfo<'info>,
    #[account(mut)]
    pub proposer: Signer<'info>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
#[instruction(deed_id: String)]
pub struct VoteDeed<'info> {
    #[account(mut, seeds = [b"deed", deed_id.as_bytes()], bump)]
    pub deed: Account<'info, DeedRecord>,
    /// CHECK: Forward reward
    #[account(mut)]
    pub nomad: AccountInfo<'info>,
    /// CHECK: Return reward
    #[account(mut)]
    pub proposer: AccountInfo<'info>,
    #[account(mut)]
    pub oracle: Signer<'info>,
    #[account(
        seeds = [b"oracle", oracle.key().as_ref()],
        bump,
        constraint = oracle_registry.is_active == true
    )]
    pub oracle_registry: Account<'info, OracleRegistry>,
    pub system_program: Program<'info, System>,
}

#[account]
#[derive(InitSpace)]
pub struct DeedRecord {
    pub nomad: Pubkey,
    pub proposer: Pubkey,
    #[max_len(32)]
    pub mission_id: String,
    pub reward_amount: u64,
    pub votes_adal: u8,
    pub votes_aram: u8,
    pub resolved: bool,
    pub timestamp: i64,
}

#[account]
#[derive(InitSpace)]
pub struct OracleRegistry {
    pub oracle: Pubkey,
    pub is_active: bool,
}

#[account]
#[derive(InitSpace)]
pub struct ProtocolStats {
    pub admin: Pubkey,
    pub total_deeds: u64,
}

#[error_code]
pub enum ErrorCode {
    #[msg("This deed has already been resolved.")]
    DeedAlreadyResolved,
    #[msg("Unauthorized protocol administrator.")]
    UnauthorizedAdmin,
}
